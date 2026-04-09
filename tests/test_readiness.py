import pytest
from fastapi import HTTPException

from app.api import health


@pytest.mark.asyncio
async def test_readiness_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ok() -> bool:
        return True

    monkeypatch.setattr(health, "_check_postgres", ok)
    monkeypatch.setattr(health, "_check_redis", ok)
    monkeypatch.setattr(health, "_check_s3", ok)

    result = await health.readiness()
    assert result["status"] == "ready"
    assert result["checks"] == {"postgres": True, "redis": True, "minio": True}


@pytest.mark.asyncio
async def test_readiness_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ok() -> bool:
        return True

    async def fail() -> bool:
        return False

    monkeypatch.setattr(health, "_check_postgres", ok)
    monkeypatch.setattr(health, "_check_redis", fail)
    monkeypatch.setattr(health, "_check_s3", ok)

    with pytest.raises(HTTPException) as exc:
        await health.readiness()
    assert exc.value.status_code == 503
