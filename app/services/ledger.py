from sqlalchemy import func, select

from app.db.models import CreditLedger, User
from app.db.session import AsyncSessionLocal


class LedgerService:
    async def get_available_balance(self, *, user_id) -> int:
        async with AsyncSessionLocal() as session:
            current_balance = (
                await session.execute(
                    select(func.coalesce(func.max(CreditLedger.balance_after), 0)).where(CreditLedger.user_id == user_id)
                )
            ).scalar_one()
            return int(current_balance)

    async def get_user_balance_by_telegram_id(self, telegram_user_id: int) -> int:
        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                return 0
        return await self.get_available_balance(user_id=user.id)

    async def get_recent_user_history_by_telegram_id(self, telegram_user_id: int, limit: int = 10) -> list[CreditLedger]:
        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                return []
            result = await session.execute(
                select(CreditLedger)
                .where(CreditLedger.user_id == user.id)
                .order_by(CreditLedger.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars())

    async def reserve_job_credits(
        self,
        *,
        user_id,
        job_id,
        amount: int,
    ) -> int:
        if amount <= 0:
            return await self.get_available_balance(user_id=user_id)

        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(CreditLedger.id).where(CreditLedger.idempotency_key == f"reserve:{job_id}")
            )
            if existing.scalar_one_or_none():
                balance = (
                    await session.execute(
                        select(func.coalesce(func.max(CreditLedger.balance_after), 0)).where(CreditLedger.user_id == user_id)
                    )
                ).scalar_one()
                return int(balance)

            current_balance = (
                await session.execute(
                    select(func.coalesce(func.max(CreditLedger.balance_after), 0)).where(CreditLedger.user_id == user_id)
                )
            ).scalar_one()
            current_balance = int(current_balance)
            if current_balance < amount:
                raise ValueError("Insufficient credits")

            new_balance = current_balance - amount
            session.add(
                CreditLedger(
                    user_id=user_id,
                    direction="debit",
                    amount=amount,
                    reason="job_reserved",
                    job_id=job_id,
                    balance_after=new_balance,
                    idempotency_key=f"reserve:{job_id}",
                    entry_status="reserved",
                )
            )
            await session.commit()
            return new_balance

    async def commit_job_credits(
        self,
        *,
        user_id,
        job_id,
        amount: int,
    ) -> None:
        if amount <= 0:
            return
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CreditLedger).where(CreditLedger.idempotency_key == f"reserve:{job_id}")
            )
            reserve_entry = result.scalar_one_or_none()
            if reserve_entry is None:
                return
            if reserve_entry.entry_status == "posted":
                return
            reserve_entry.reason = "job_charged"
            reserve_entry.entry_status = "posted"
            await session.commit()

    async def refund_job_credits(
        self,
        *,
        user_id,
        job_id,
        amount: int,
        reason: str = "job_failed_refund",
    ) -> None:
        if amount <= 0:
            return

        async with AsyncSessionLocal() as session:
            current_balance = (
                await session.execute(
                    select(func.coalesce(func.max(CreditLedger.balance_after), 0)).where(CreditLedger.user_id == user_id)
                )
            ).scalar_one()

            refund_entry = CreditLedger(
                user_id=user_id,
                direction="credit",
                amount=amount,
                reason=reason,
                job_id=job_id,
                balance_after=int(current_balance) + amount,
                idempotency_key=f"refund:{job_id}",
                entry_status="posted",
            )
            session.add(refund_entry)
            await session.commit()

    async def grant_welcome_credits(
        self,
        *,
        user_id,
        amount: int,
    ) -> None:
        if amount <= 0:
            return
        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(CreditLedger.id).where(CreditLedger.user_id == user_id, CreditLedger.reason == "welcome_bonus")
            )
            if existing.scalar_one_or_none():
                return
            session.add(
                CreditLedger(
                    user_id=user_id,
                    direction="credit",
                    amount=amount,
                    reason="welcome_bonus",
                    balance_after=amount,
                    idempotency_key=f"welcome:{user_id}",
                    entry_status="posted",
                )
            )
            await session.commit()

    async def grant_purchase_credits(
        self,
        *,
        user_id,
        purchase_id,
        amount: int,
        reason: str = "purchase_credit_grant",
    ) -> None:
        if amount <= 0:
            return
        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(CreditLedger.id).where(CreditLedger.idempotency_key == f"purchase:{purchase_id}")
            )
            if existing.scalar_one_or_none():
                return
            current_balance = (
                await session.execute(
                    select(func.coalesce(func.max(CreditLedger.balance_after), 0)).where(CreditLedger.user_id == user_id)
                )
            ).scalar_one()
            session.add(
                CreditLedger(
                    user_id=user_id,
                    direction="credit",
                    amount=amount,
                    reason=reason,
                    purchase_id=purchase_id,
                    balance_after=int(current_balance) + amount,
                    idempotency_key=f"purchase:{purchase_id}",
                    entry_status="posted",
                )
            )
            await session.commit()
