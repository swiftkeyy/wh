from functools import lru_cache
import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_name: str = Field(default="WHYNOT Photoshop", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    public_base_url: str = Field(alias="PUBLIC_BASE_URL")
    auto_set_webhook: bool = Field(default=False, alias="AUTO_SET_WEBHOOK")
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(alias="TELEGRAM_WEBHOOK_SECRET")
    postgres_dsn: str = Field(alias="POSTGRES_DSN")
    redis_url: str = Field(alias="REDIS_URL")
    s3_endpoint_url: str = Field(alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(alias="S3_SECRET_KEY")
    s3_bucket: str = Field(alias="S3_BUCKET")
    s3_region: str = Field(alias="S3_REGION")
    ai_default_provider: str = Field(alias="AI_DEFAULT_PROVIDER")
    ai_fallback_provider: str = Field(alias="AI_FALLBACK_PROVIDER")
    remove_bg_api_key: str | None = Field(default=None, alias="REMOVE_BG_API_KEY")
    google_genai_api_key: str | None = Field(default=None, alias="GOOGLE_GENAI_API_KEY")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    prompt_library_version: str = Field(alias="PROMPT_LIBRARY_VERSION")
    default_free_credits: int = Field(default=8, alias="DEFAULT_FREE_CREDITS")
    max_images_per_job: int = Field(default=4, alias="MAX_IMAGES_PER_JOB")
    max_upload_mb: int = Field(default=15, alias="MAX_UPLOAD_MB")
    job_pricing_json: str = Field(default='{"transparent_bg":2}', alias="JOB_PRICING_JSON")
    purchase_packs_json: str = Field(default="[]", alias="PURCHASE_PACKS_JSON")
    subscription_plans_json: str = Field(default="[]", alias="SUBSCRIPTION_PLANS_JSON")
    admin_telegram_ids: str = Field(default="", alias="ADMIN_TELEGRAM_IDS")

    @property
    def job_pricing(self) -> dict[str, int]:
        return {key: int(value) for key, value in json.loads(self.job_pricing_json).items()}

    @property
    def purchase_packs(self) -> list[dict]:
        return list(json.loads(self.purchase_packs_json))

    @property
    def subscription_plans(self) -> list[dict]:
        return list(json.loads(self.subscription_plans_json))

    @property
    def admin_ids(self) -> set[int]:
        if not self.admin_telegram_ids.strip():
            return set()
        return {int(value.strip()) for value in self.admin_telegram_ids.split(",") if value.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
