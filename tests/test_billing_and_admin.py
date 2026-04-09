from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.admin import AdminService
from app.services.billing import BillingService
from app.tasks.subscriptions import expire_due_subscriptions_task


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def __iter__(self):
        return iter(self.value)


class BillingSession:
    def __init__(self, user, purchase=None, subscription=None, purchases=None, ledger=None, failed_jobs=None):
        self.user = user
        self.purchase = purchase
        self.subscription = subscription
        self.purchases = purchases or []
        self.ledger = ledger or []
        self.failed_jobs = failed_jobs or []
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def execute(self, query):
        query_text = str(query)
        if "FROM users" in query_text:
            return FakeScalarResult(self.user)
        if "FROM purchases" in query_text and "ORDER BY purchases.created_at DESC" in query_text:
            return FakeScalarResult(self.purchases)
        if "FROM purchases" in query_text:
            return FakeScalarResult(self.purchase)
        if "FROM subscriptions" in query_text:
            return FakeScalarResult(self.subscription)
        if "FROM credit_ledger" in query_text and "ORDER BY credit_ledger.created_at DESC" in query_text:
            return FakeScalarResult(self.ledger)
        if "FROM jobs" in query_text:
            return FakeScalarResult(self.failed_jobs)
        raise AssertionError(f"Unexpected query: {query_text}")

    def add(self, value):
        self.added.append(value)
        if value.__class__.__name__ == "Purchase":
            value.id = uuid4()
            self.purchase = value
        if value.__class__.__name__ == "Subscription":
            self.subscription = value

    async def commit(self):
        return None

    async def refresh(self, value):
        return None


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_create_pack_purchase_returns_stars_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(id="user-1", telegram_user_id=100)
    session = BillingSession(user=user)
    monkeypatch.setattr("app.services.billing.AsyncSessionLocal", lambda: SessionContext(session))

    service = BillingService()
    intent = await service.create_pack_purchase(
        telegram_user_id=100,
        pack={"sku": "pack_small", "price_stars": 299},
    )
    assert intent.provider == "telegram_stars"
    assert intent.currency == "XTR"
    assert intent.checkout_payload.startswith("purchase:")


@pytest.mark.asyncio
async def test_confirm_successful_pack_payment_grants_credits(monkeypatch: pytest.MonkeyPatch) -> None:
    purchase = SimpleNamespace(id=uuid4(), purchase_type="credit_pack", sku="pack_small", status="pending")
    user = SimpleNamespace(id="user-1", telegram_user_id=100)
    session = BillingSession(user=user, purchase=purchase)
    monkeypatch.setattr("app.services.billing.AsyncSessionLocal", lambda: SessionContext(session))

    fake_ledger = SimpleNamespace(grant_purchase_credits=AsyncMock())
    fake_pricing = SimpleNamespace(
        get_purchase_pack=lambda sku: {"sku": sku, "title": "30 кредитов", "credits": 30},
        get_subscription_plan=lambda code: None,
    )
    service = BillingService(ledger_service=fake_ledger, pricing_policy=fake_pricing)
    text = await service.confirm_successful_payment(
        telegram_user_id=100,
        payload=f"purchase:{purchase.id}",
        telegram_payment_charge_id="tg-1",
        provider_payment_charge_id="provider-1",
        total_amount=299,
    )
    assert purchase.status == "paid"
    assert "30 кредитов" in text
    fake_ledger.grant_purchase_credits.assert_awaited_once()


@pytest.mark.asyncio
async def test_expire_due_subscriptions_marks_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(id="user-1", telegram_user_id=100)
    subscription = SimpleNamespace(
        id="sub-1",
        plan_code="lite",
        status="active",
        current_period_end=datetime.now(UTC) - timedelta(days=1),
    )
    session = BillingSession(user=user, subscription=[subscription])

    class _ExpireSession(SessionContext):
        async def __aenter__(self):
            return session

    monkeypatch.setattr("app.services.billing.AsyncSessionLocal", lambda: _ExpireSession(session))
    service = BillingService()
    count = await service.expire_due_subscriptions()
    assert count == 1
    assert subscription.status == "expired"


def test_expire_due_subscriptions_task(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.tasks.subscriptions.BillingService.expire_due_subscriptions", AsyncMock(return_value=2))
    result = expire_due_subscriptions_task.run()
    assert result == {"expired": 2}


@pytest.mark.asyncio
async def test_admin_audit_snapshot_collects_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    session = BillingSession(
        user=SimpleNamespace(id="admin"),
        purchases=[SimpleNamespace(sku="pack_small")],
        ledger=[SimpleNamespace(reason="welcome_bonus")],
        failed_jobs=[SimpleNamespace(error_code="job_runner_failed")],
    )
    monkeypatch.setattr("app.services.admin.AsyncSessionLocal", lambda: SessionContext(session))
    service = AdminService()
    snapshot = await service.get_audit_snapshot(limit=5)
    assert len(snapshot["purchases"]) == 1
    assert len(snapshot["ledger"]) == 1
    assert len(snapshot["failed_jobs"]) == 1
