from sqlalchemy import select

from app.db.models import CreditLedger, Payment, Purchase
from app.db.session import AsyncSessionLocal


class AlertingService:
    async def get_payment_integrity_issues(self, limit: int = 20) -> list[dict]:
        issues: list[dict] = []
        async with AsyncSessionLocal() as session:
            failed_payments_result = await session.execute(
                select(Payment).where(Payment.status != "paid").order_by(Payment.created_at.desc()).limit(limit)
            )
            for payment in failed_payments_result.scalars():
                issues.append(
                    {
                        "type": "payment_not_paid",
                        "payment_id": str(payment.id),
                        "purchase_id": str(payment.purchase_id),
                        "status": payment.status,
                    }
                )

            purchases_result = await session.execute(
                select(Purchase).where(Purchase.status == "paid").order_by(Purchase.created_at.desc()).limit(limit)
            )
            purchases = list(purchases_result.scalars())
            for purchase in purchases:
                ledger_result = await session.execute(
                    select(CreditLedger.id).where(CreditLedger.purchase_id == purchase.id)
                )
                ledger_entry = ledger_result.scalar_one_or_none()
                if purchase.purchase_type in {"credit_pack", "subscription"} and ledger_entry is None:
                    issues.append(
                        {
                            "type": "missing_ledger_grant",
                            "purchase_id": str(purchase.id),
                            "sku": purchase.sku,
                            "purchase_type": purchase.purchase_type,
                        }
                    )
        return issues
