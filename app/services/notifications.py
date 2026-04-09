from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.core.config import settings


class TelegramNotificationService:
    def __init__(self, bot: Bot | None = None) -> None:
        self.bot = bot or Bot(token=settings.telegram_bot_token)

    async def send_remove_bg_result(
        self,
        chat_id: int,
        image_bytes: bytes,
        caption: str,
        filename: str = "whynot-photoshop-result.png",
        mime_type: str = "image/png",
    ) -> None:
        payload = BufferedInputFile(file=image_bytes, filename=filename)
        if self._can_send_as_photo(filename=filename, mime_type=mime_type, image_bytes=image_bytes):
            await self.bot.send_photo(chat_id=chat_id, photo=payload, caption=caption)
            return
        await self.bot.send_document(chat_id=chat_id, document=payload, caption=caption)

    async def send_job_failed(self, chat_id: int, job_id: str) -> None:
        await self.bot.send_message(
            chat_id=chat_id,
            text=(
                "Не удалось завершить обработку.\n"
                f"Job ID: `{job_id}`\n"
                "Мы сохранили задачу для разбора. Если списались кредиты, дальше должна сработать логика возврата."
            ),
            parse_mode="Markdown",
        )

    @staticmethod
    def _can_send_as_photo(filename: str, mime_type: str, image_bytes: bytes) -> bool:
        allowed_mime = {"image/jpeg", "image/png"}
        allowed_ext = (".jpg", ".jpeg", ".png")
        if mime_type not in allowed_mime:
            return False
        if not filename.lower().endswith(allowed_ext):
            return False
        max_photo_size_bytes = 10 * 1024 * 1024
        return len(image_bytes) <= max_photo_size_bytes
