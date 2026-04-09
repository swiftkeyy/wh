from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.bootstrap import configure_webhook
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging(settings.log_level)

app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
)
app.include_router(api_router)

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def startup_event() -> None:
    if settings.auto_set_webhook:
        await configure_webhook(drop_pending_updates=False)
