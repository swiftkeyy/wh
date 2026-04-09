from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.infra.ai_providers import GeneratedAsset, ImageGenerationResult
from app.services.job_runner import JobRunner
from app.services.job_service import JobService


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, user):
        self.user = user
        self.job = None
        self.job_input = None
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def execute(self, query):
        query_text = str(query)
        if "FROM users" in query_text:
            return FakeScalarResult(self.user)
        if "FROM jobs" in query_text:
            return FakeScalarResult(self.job)
        if "FROM job_inputs" in query_text:
            return FakeScalarResult(self.job_input)
        raise AssertionError(f"Unexpected query: {query_text}")

    def add(self, value):
        self.added.append(value)
        table_name = value.__class__.__name__
        if table_name == "Job":
            value.id = uuid4()
            self.job = value
        if table_name == "JobInput":
            self.job_input = value

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, value):
        return None


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_job_service_to_runner_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(id="user-1", telegram_user_id=10001)
    fake_session = FakeSession(user=user)

    monkeypatch.setattr("app.services.job_service.AsyncSessionLocal", lambda: FakeSessionContext(fake_session))
    monkeypatch.setattr("app.services.job_runner.AsyncSessionLocal", lambda: FakeSessionContext(fake_session))

    captured_delay = {}

    class FakeStorage:
        def __init__(self):
            self.saved = {}

        def upload_bytes(self, key, body, content_type):
            self.saved[key] = body
            return key

        def download_bytes(self, key):
            return self.saved[key]

        def public_url(self, key):
            return f"http://storage/{key}"

    fake_storage = FakeStorage()
    async def reserve_job_credits(**kwargs):
        return 6

    fake_ledger = SimpleNamespace(
        reserve_job_credits=reserve_job_credits,
        commit_job_credits=AsyncMock(),
        refund_job_credits=AsyncMock(),
    )
    fake_notifications = SimpleNamespace(send_remove_bg_result=AsyncMock(), send_job_failed=AsyncMock())
    fake_provider = SimpleNamespace(
        generate=AsyncMock(
            return_value=ImageGenerationResult(
                provider_job_id="provider-1",
                assets=[GeneratedAsset(bytes_data=b"result", mime_type="image/png", width=256, height=256)],
                moderation_flags=[],
            )
        )
    )
    fake_registry = SimpleNamespace(get=lambda provider_name: fake_provider)

    def fake_delay(job_id):
        captured_delay["job_id"] = job_id

    monkeypatch.setattr("app.services.job_service.process_image_job.delay", fake_delay)

    job_service = JobService(storage=fake_storage, ledger=fake_ledger)
    created_job_id = await job_service.create_remove_bg_job(
        telegram_user_id=10001,
        image_bytes=b"source-image",
        mime_type="image/jpeg",
    )

    runner = JobRunner(
        storage=fake_storage,
        providers=fake_registry,
        notifications=fake_notifications,
        ledger=fake_ledger,
    )
    result = await runner.run(created_job_id)

    assert captured_delay["job_id"] == created_job_id
    assert result["status"] == "succeeded"
    fake_notifications.send_remove_bg_result.assert_awaited_once()
    fake_ledger.commit_job_credits.assert_awaited_once()
