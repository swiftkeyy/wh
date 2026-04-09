import asyncio

from app.services.billing import BillingService
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(TimeoutError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    queue="billing",
)
def expire_due_subscriptions_task(self) -> dict[str, int]:
    billing = BillingService()
    expired = asyncio.run(billing.expire_due_subscriptions())
    return {"expired": expired}
