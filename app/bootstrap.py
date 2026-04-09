import argparse
import asyncio

from aiogram import Bot
from botocore.exceptions import ClientError

from app.core.config import settings
from app.infra.storage import StorageService


async def ensure_bucket_exists() -> None:
    storage = StorageService()
    try:
        storage.client.head_bucket(Bucket=storage.bucket)
    except ClientError:
        storage.client.create_bucket(Bucket=storage.bucket)


async def configure_webhook(drop_pending_updates: bool = False) -> None:
    if not settings.public_base_url or not settings.telegram_webhook_secret:
        raise ValueError("PUBLIC_BASE_URL and TELEGRAM_WEBHOOK_SECRET must be configured")

    bot = Bot(token=settings.telegram_bot_token)
    webhook_url = f"{settings.public_base_url.rstrip('/')}/webhooks/telegram"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.telegram_webhook_secret,
        drop_pending_updates=drop_pending_updates,
        allowed_updates=["message", "callback_query"],
    )
    await bot.session.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap WHYNOT Photoshop runtime dependencies")
    parser.add_argument("--ensure-bucket", action="store_true")
    parser.add_argument("--set-webhook", action="store_true")
    parser.add_argument("--drop-pending-updates", action="store_true")
    args = parser.parse_args()

    if args.ensure_bucket:
        await ensure_bucket_exists()
    if args.set_webhook:
        await configure_webhook(drop_pending_updates=args.drop_pending_updates)


if __name__ == "__main__":
    asyncio.run(main())
