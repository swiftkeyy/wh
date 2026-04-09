from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "lumiaflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_default_queue="image_jobs",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=180,
    task_soft_time_limit=150,
)
