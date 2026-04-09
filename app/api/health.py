from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, status
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.infra.storage import StorageService
from app.services.alerts import AlertingService

router = APIRouter()
alerting_service = AlertingService()


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict:
    checks = {
        "postgres": await _check_postgres(),
        "redis": await _check_redis(),
        "minio": await _check_s3(),
    }
    if not all(checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "checks": checks},
        )
    return {"status": "ready", "checks": checks}


@router.get("/alerts")
async def alerts() -> dict:
    issues = await alerting_service.get_payment_integrity_issues()
    return {"issues": issues, "count": len(issues)}


async def _check_postgres() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    client = redis_from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await client.ping()
        return True
    except Exception:
        return False
    finally:
        await client.aclose()


async def _check_s3() -> bool:
    storage = StorageService()
    try:
        storage.client.head_bucket(Bucket=storage.bucket)
        return True
    except (ClientError, BotoCoreError, Exception):
        return False
