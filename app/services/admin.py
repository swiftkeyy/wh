from sqlalchemy import select

from app.core.config import settings
from app.db.models import AdminAction, CreditLedger, Job, Purchase, User
from app.db.session import AsyncSessionLocal
from app.services.alerts import AlertingService


class AdminService:
    def __init__(self, alerting_service: AlertingService | None = None) -> None:
        self.alerting_service = alerting_service or AlertingService()

    def is_admin(self, telegram_user_id: int) -> bool:
        return telegram_user_id in settings.admin_ids

    async def adjust_credits(
        self,
        *,
        admin_telegram_user_id: int,
        target_telegram_user_id: int,
        direction: str,
        amount: int,
        reason: str,
    ) -> int:
        if direction not in {"credit", "debit"}:
            raise ValueError("direction must be credit or debit")
        if amount <= 0:
            raise ValueError("amount must be positive")

        async with AsyncSessionLocal() as session:
            admin_result = await session.execute(select(User).where(User.telegram_user_id == admin_telegram_user_id))
            admin_user = admin_result.scalar_one_or_none()
            target_result = await session.execute(select(User).where(User.telegram_user_id == target_telegram_user_id))
            target_user = target_result.scalar_one()

            last_balance_result = await session.execute(
                select(CreditLedger.balance_after)
                .where(CreditLedger.user_id == target_user.id)
                .order_by(CreditLedger.created_at.desc())
                .limit(1)
            )
            last_balance = last_balance_result.scalar_one_or_none() or 0
            new_balance = last_balance + amount if direction == "credit" else last_balance - amount
            if new_balance < 0:
                raise ValueError("cannot debit below zero")

            ledger_entry = CreditLedger(
                user_id=target_user.id,
                direction=direction,
                amount=amount,
                reason=reason,
                balance_after=new_balance,
                idempotency_key=f"admin:{admin_telegram_user_id}:{target_telegram_user_id}:{direction}:{amount}:{reason}",
                entry_status="posted",
            )
            session.add(ledger_entry)

            if admin_user is not None:
                session.add(
                    AdminAction(
                        admin_user_id=admin_user.id,
                        action_type="adjust_credits",
                        target_type="user",
                        target_id=str(target_user.id),
                        note=f"{direction} {amount}: {reason}",
                    )
                )

            await session.commit()
            return new_balance

    async def get_audit_snapshot(self, limit: int = 5) -> dict[str, list]:
        async with AsyncSessionLocal() as session:
            purchases_result = await session.execute(
                select(Purchase).order_by(Purchase.created_at.desc()).limit(limit)
            )
            ledger_result = await session.execute(
                select(CreditLedger).order_by(CreditLedger.created_at.desc()).limit(limit)
            )
            failed_jobs_result = await session.execute(
                select(Job).where(Job.status == "failed").order_by(Job.updated_at.desc()).limit(limit)
            )
            return {
                "purchases": list(purchases_result.scalars()),
                "ledger": list(ledger_result.scalars()),
                "failed_jobs": list(failed_jobs_result.scalars()),
            }

    async def get_audit_report_text(self, limit: int = 5) -> str:
        snapshot = await self.get_audit_snapshot(limit=limit)
        issues = await self.alerting_service.get_payment_integrity_issues(limit=limit)
        purchases = snapshot["purchases"]
        ledger = snapshot["ledger"]
        failed_jobs = snapshot["failed_jobs"]
        return (
            "**Admin Audit**\n\n"
            "Purchases:\n"
            + ("\n".join([f"- {item.purchase_type} {item.sku} | {item.status} | {item.amount_minor} {item.currency}" for item in purchases]) or "- none")
            + "\n\nLedger:\n"
            + ("\n".join([f"- {item.direction} {item.amount} | {item.reason} | balance={item.balance_after}" for item in ledger]) or "- none")
            + "\n\nFailed jobs:\n"
            + ("\n".join([f"- {item.id} | {item.job_type} | {item.error_code}" for item in failed_jobs]) or "- none")
            + "\n\nAlerts:\n"
            + ("\n".join([f"- {item['type']} | purchase={item.get('purchase_id', 'n/a')} | status={item.get('status', 'n/a')}" for item in issues]) or "- none")
        )
