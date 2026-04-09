import asyncio

from app.services.job_runner import JobRunner
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(TimeoutError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 4},
    queue="image_jobs",
)
def process_image_job(self, job_id: str) -> dict[str, str]:
    runner = JobRunner()
    return asyncio.run(runner.run(job_id))
