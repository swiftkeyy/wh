from sqlalchemy import select

from app.db.models import User, UserProfile
from app.db.session import AsyncSessionLocal
from app.services.ledger import LedgerService
from app.services.pricing_policy import PricingPolicyService


class UserContextService:
    def __init__(
        self,
        ledger_service: LedgerService | None = None,
        pricing_policy: PricingPolicyService | None = None,
    ) -> None:
        self.ledger_service = ledger_service or LedgerService()
        self.pricing_policy = pricing_policy or PricingPolicyService()

    async def ensure_user(self, telegram_user_id: int, username: str | None, language_code: str | None) -> User:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = result.scalar_one_or_none()
            if user:
                if username is not None:
                    user.username = username
                if language_code:
                    user.language_code = language_code
                await session.commit()
                return user

            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                language_code=language_code or "ru",
            )
            session.add(user)
            await session.flush()
            session.add(UserProfile(user_id=user.id, locale="ru-RU"))
            await session.commit()
            await session.refresh(user)
            await self.ledger_service.grant_welcome_credits(
                user_id=user.id,
                amount=self.pricing_policy.get_welcome_credits(),
            )
            return user

    async def set_pending_mode(self, telegram_user_id: int, mode: str | None) -> None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserProfile).join(User).where(User.telegram_user_id == telegram_user_id))
            profile = result.scalar_one_or_none()
            if not profile:
                return
            profile.pending_mode = mode
            await session.commit()

    async def get_pending_mode(self, telegram_user_id: int) -> str | None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserProfile.pending_mode).join(User).where(User.telegram_user_id == telegram_user_id))
            return result.scalar_one_or_none()
