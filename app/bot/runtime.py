from aiogram import Bot, Dispatcher
from aiogram.types import Update

from app.bot.handlers import router
from app.core.config import settings

bot = Bot(token=settings.telegram_bot_token)
dispatcher = Dispatcher()
dispatcher.include_router(router)


async def handle_update(payload: dict) -> None:
    update = Update.model_validate(payload)
    await dispatcher.feed_update(bot, update)
