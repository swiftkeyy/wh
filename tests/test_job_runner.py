from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.infra.ai_providers import GeneratedAsset, ImageGenerationResult
from app.services.job_runner import JobRunner


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class FakeSession:
    def __init__(self, job, user, job_input):
        self.job = job
        self.user = user
        self.job_input = job_input
        self.added = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def execute(self, query):
        query_text = str(query)
        if "FROM jobs" in query_text:
            return FakeScalarResult(self.job)
        if "FROM users" in query_text:
            return FakeScalarResult(self.user)
        if "FROM job_inputs" in query_text:
            return FakeScalarResult(self.job_input)
        raise AssertionError(f"Unexpected query: {query_text}")

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_job_runner_sends_result(monkeypatch: pytest.MonkeyPatch) -> None:
    job = SimpleNamespace(
        id="job-1",
        user_id="user-1",
        provider="remove_bg",
        prompt_final="remove background",
        status="pending",
        error_code=None,
        credits_reserved=2,
        credits_charged=0,
    )
    user = SimpleNamespace(telegram_user_id=12345)
    job_input = SimpleNamespace(
        storage_key="input-key",
        public_url="http://storage/input.jpg",
        metadata_json={"mime_type": "image/jpeg"},
    )

    fake_storage = SimpleNamespace(
        download_bytes=lambda key: b"source-bytes",
        upload_bytes=lambda key, body, content_type: key,
        public_url=lambda key: f"http://storage/{key}",
    )
    fake_provider = SimpleNamespace(
        generate=AsyncMock(
            return_value=ImageGenerationResult(
                provider_job_id="provider-1",
                assets=[
                    GeneratedAsset(
                        bytes_data=b"result-png",
                        mime_type="image/png",
                        width=512,
                        height=512,
                    )
                ],
                moderation_flags=[],
            )
        )
    )
    fake_registry = SimpleNamespace(get=lambda provider_name: fake_provider)
    fake_notifications = SimpleNamespace(send_remove_bg_result=AsyncMock(), send_job_failed=AsyncMock())
    fake_ledger = SimpleNamespace(commit_job_credits=AsyncMock(), refund_job_credits=AsyncMock())

    fake_session = FakeSession(job=job, user=user, job_input=job_input)

    async def fake_session_factory():
        return fake_session

    class _SessionContext:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("app.services.job_runner.AsyncSessionLocal", lambda: _SessionContext())

    runner = JobRunner(
        storage=fake_storage,
        providers=fake_registry,
        notifications=fake_notifications,
        ledger=fake_ledger,
    )

    result = await runner.run("job-1")
    assert result["status"] == "succeeded"
    assert job.status == "succeeded"
    assert job.credits_charged == 2
    fake_notifications.send_remove_bg_result.assert_awaited_once()
    fake_ledger.commit_job_credits.assert_awaited_once()
    fake_ledger.refund_job_credits.assert_not_called()


@pytest.mark.asyncio
async def test_job_runner_refunds_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    job = SimpleNamespace(
        id="job-2",
        user_id="user-1",
        provider="remove_bg",
        prompt_final="remove background",
        status="pending",
        error_code=None,
        credits_reserved=2,
        credits_charged=0,
    )
    user = SimpleNamespace(telegram_user_id=12345)
    job_input = SimpleNamespace(
        storage_key="input-key",
        public_url="http://storage/input.jpg",
        metadata_json={"mime_type": "image/jpeg"},
    )

    fake_storage = SimpleNamespace(
        download_bytes=lambda key: b"source-bytes",
        upload_bytes=lambda key, body, content_type: key,
        public_url=lambda key: f"http://storage/{key}",
    )
    fake_provider = SimpleNamespace(generate=AsyncMock(side_effect=RuntimeError("provider failed")))
    fake_registry = SimpleNamespace(get=lambda provider_name: fake_provider)
    fake_notifications = SimpleNamespace(send_remove_bg_result=AsyncMock(), send_job_failed=AsyncMock())
    fake_ledger = SimpleNamespace(commit_job_credits=AsyncMock(), refund_job_credits=AsyncMock())

    fake_session = FakeSession(job=job, user=user, job_input=job_input)

    class _SessionContext:
        async def __aenter__(self):
            return fake_session

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("app.services.job_runner.AsyncSessionLocal", lambda: _SessionContext())

    runner = JobRunner(
        storage=fake_storage,
        providers=fake_registry,
        notifications=fake_notifications,
        ledger=fake_ledger,
    )

    with pytest.raises(RuntimeError):
        await runner.run("job-2")
    assert job.status == "failed"
    fake_ledger.refund_job_credits.assert_awaited_once()
    fake_notifications.send_job_failed.assert_awaited_once()
