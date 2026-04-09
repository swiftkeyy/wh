from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from aiogram import Bot
from aiogram.types import LabeledPrice
from sqlalchemy import select

from app.db.models import Payment, Purchase, Subscription, User
from app.db.session import AsyncSessionLocal
from app.services.analytics import AnalyticsService
from app.services.ledger import LedgerService
from app.services.pricing_policy import PricingPolicyService


@dataclass
class PurchaseIntent:
    purchase_id: str
    sku: str
    amount_minor: int
    currency: str
    status: str
    provider: str
    checkout_payload: str


class BillingService:
    def __init__(
        self,
        analytics_service: AnalyticsService | None = None,
        ledger_service: LedgerService | None = None,
        pricing_policy: PricingPolicyService | None = None,
    ) -> None:
        self.analytics_service = analytics_service or AnalyticsService()
        self.ledger_service = ledger_service or LedgerService()
        self.pricing_policy = pricing_policy or PricingPolicyService()

    async def create_pack_purchase(self, *, telegram_user_id: int, pack: dict) -> PurchaseIntent:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = result.scalar_one()
            purchase = Purchase(
                user_id=user.id,
                purchase_type="credit_pack",
                sku=pack["sku"],
                status="pending",
                amount_minor=int(pack["price_stars"]),
                currency="XTR",
            )
            session.add(purchase)
            await session.commit()
            await session.refresh(purchase)
            self.analytics_service.track(
                "purchase_intent_created",
                {
                    "purchase_id": str(purchase.id),
                    "purchase_type": "credit_pack",
                    "sku": purchase.sku,
                    "amount_stars": purchase.amount_minor,
                },
            )
            return PurchaseIntent(
                purchase_id=str(purchase.id),
                sku=purchase.sku,
                amount_minor=purchase.amount_minor,
                currency=purchase.currency,
                status=purchase.status,
                provider="telegram_stars",
                checkout_payload=f"purchase:{purchase.id}",
            )

    async def create_subscription_purchase(self, *, telegram_user_id: int, plan: dict) -> PurchaseIntent:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = result.scalar_one()
            purchase = Purchase(
                user_id=user.id,
                purchase_type="subscription",
                sku=plan["code"],
                status="pending",
                amount_minor=int(plan["price_stars"]),
                currency="XTR",
            )
            session.add(purchase)
            await session.commit()
            await session.refresh(purchase)
            self.analytics_service.track(
                "purchase_intent_created",
                {
                    "purchase_id": str(purchase.id),
                    "purchase_type": "subscription",
                    "sku": purchase.sku,
                    "amount_stars": purchase.amount_minor,
                },
            )
            return PurchaseIntent(
                purchase_id=str(purchase.id),
                sku=purchase.sku,
                amount_minor=purchase.amount_minor,
                currency=purchase.currency,
                status=purchase.status,
                provider="telegram_stars",
                checkout_payload=f"purchase:{purchase.id}",
            )

    async def send_stars_invoice(
        self,
        *,
        bot: Bot,
        chat_id: int,
        title: str,
        description: str,
        intent: PurchaseIntent,
    ) -> None:
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=intent.checkout_payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=int(intent.amount_minor))],
        )
        self.analytics_service.track(
            "stars_invoice_sent",
            {
                "chat_id": chat_id,
                "purchase_id": intent.purchase_id,
                "sku": intent.sku,
                "amount_stars": intent.amount_minor,
            },
        )

    async def answer_pre_checkout(
        self,
        *,
        bot: Bot,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: str | None = None,
    ) -> None:
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query_id,
            ok=ok,
            error_message=error_message,
        )

    async def confirm_successful_payment(
        self,
        *,
        telegram_user_id: int,
        payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
        total_amount: int,
    ) -> str:
        if not payload.startswith("purchase:"):
            raise ValueError("Unsupported payment payload")
        purchase_id = UUID(payload.split(":", 1)[1])

        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = user_result.scalar_one()
            purchase_result = await session.execute(select(Purchase).where(Purchase.id == purchase_id))
            purchase = purchase_result.scalar_one()

            purchase.status = "paid"
            session.add(
                Payment(
                    purchase_id=purchase.id,
                    provider="telegram_stars",
                    provider_payment_id=telegram_payment_charge_id,
                    status="paid",
                    idempotency_key=f"tgstars:{telegram_payment_charge_id}",
                    raw_payload={
                        "provider_payment_charge_id": provider_payment_charge_id,
                        "telegram_payment_charge_id": telegram_payment_charge_id,
                        "total_amount": total_amount,
                    },
                )
            )

            if purchase.purchase_type == "credit_pack":
                pack = self.pricing_policy.get_purchase_pack(purchase.sku)
                if not pack:
                    raise ValueError("Pack not found")
                await session.commit()
                await self.ledger_service.grant_purchase_credits(
                    user_id=user.id,
                    purchase_id=purchase.id,
                    amount=int(pack["credits"]),
                )
                self.analytics_service.track(
                    "payment_succeeded",
                    {
                        "purchase_id": str(purchase.id),
                        "purchase_type": purchase.purchase_type,
                        "sku": purchase.sku,
                        "amount_stars": total_amount,
                        "credits_granted": int(pack["credits"]),
                    },
                )
                return f"Пакет {pack['title']} оплачен. Начислено {pack['credits']} кредитов."

            plan = self.pricing_policy.get_subscription_plan(purchase.sku)
            if not plan:
                raise ValueError("Subscription plan not found")

            now = datetime.now(UTC)
            current_period_end = now + timedelta(days=30)
            sub_result = await session.execute(
                select(Subscription).where(Subscription.user_id == user.id, Subscription.plan_code == purchase.sku)
            )
            subscription = sub_result.scalar_one_or_none()
            if subscription is None:
                subscription = Subscription(
                    user_id=user.id,
                    plan_code=purchase.sku,
                    status="active",
                    renews_at=current_period_end,
                    current_period_end=current_period_end,
                    provider="telegram_stars",
                )
                session.add(subscription)
            else:
                subscription.status = "active"
                subscription.renews_at = current_period_end
                subscription.current_period_end = current_period_end

            await session.commit()
            await self.ledger_service.grant_purchase_credits(
                user_id=user.id,
                purchase_id=purchase.id,
                amount=int(plan["credits_monthly"]),
                reason="subscription_credit_grant",
            )
            self.analytics_service.track(
                "subscription_activated",
                {
                    "purchase_id": str(purchase.id),
                    "plan_code": purchase.sku,
                    "amount_stars": total_amount,
                    "credits_granted": int(plan["credits_monthly"]),
                    "current_period_end": current_period_end.isoformat(),
                },
            )
            return f"Подписка {plan['title']} активирована. Начислено {plan['credits_monthly']} кредитов."

    async def expire_due_subscriptions(self) -> int:
        now = datetime.now(UTC)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.status == "active", Subscription.current_period_end < now)
            )
            subscriptions = list(result.scalars())
            for subscription in subscriptions:
                subscription.status = "expired"
            await session.commit()
            for subscription in subscriptions:
                self.analytics_service.track(
                    "subscription_expired",
                    {
                        "subscription_id": str(subscription.id),
                        "plan_code": subscription.plan_code,
                    },
                )
            return len(subscriptions)

    async def renew_active_subscription(self, subscription_id) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Subscription).where(Subscription.id == subscription_id))
            subscription = result.scalar_one_or_none()
            if subscription is None or subscription.status != "active":
                return False
            plan = self.pricing_policy.get_subscription_plan(subscription.plan_code)
            if not plan:
                return False
            subscription.current_period_end = (subscription.current_period_end or datetime.now(UTC)) + timedelta(days=30)
            subscription.renews_at = subscription.current_period_end
            await session.commit()
            await self.ledger_service.grant_purchase_credits(
                user_id=subscription.user_id,
                purchase_id=f"renewal:{subscription.id}:{subscription.current_period_end.date()}",
                amount=int(plan["credits_monthly"]),
                reason="subscription_renewal_credit_grant",
            )
            self.analytics_service.track(
                "subscription_renewed",
                {
                    "subscription_id": str(subscription.id),
                    "plan_code": subscription.plan_code,
                    "current_period_end": subscription.current_period_end.isoformat(),
                },
            )
            return True

    async def get_active_subscription_summary(self, telegram_user_id: int) -> str:
        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                return "Подписка не найдена."
            sub_result = await session.execute(
                select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
            )
            subscription = sub_result.scalar_one_or_none()
            if subscription is None:
                return "Активной подписки нет."
            renew_at = subscription.current_period_end.strftime("%Y-%m-%d") if subscription.current_period_end else "n/a"
            return f"Активная подписка: {subscription.plan_code}, статус: {subscription.status}, до {renew_at}"

    async def get_recent_purchase_history(self, telegram_user_id: int, limit: int = 10) -> list[Purchase]:
        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                return []
            result = await session.execute(
                select(Purchase).where(Purchase.user_id == user.id).order_by(Purchase.created_at.desc()).limit(limit)
            )
            return list(result.scalars())
