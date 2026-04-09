from sqlalchemy import select

from app.db.models import Job, JobInput, JobResult, User
from app.db.session import AsyncSessionLocal
from app.infra.ai_providers import ImageGenerationRequest, ProviderRegistry
from app.infra.storage import StorageService
from app.services.ledger import LedgerService
from app.services.notifications import TelegramNotificationService


class JobRunner:
    def __init__(
        self,
        storage: StorageService | None = None,
        providers: ProviderRegistry | None = None,
        notifications: TelegramNotificationService | None = None,
        ledger: LedgerService | None = None,
    ) -> None:
        self.storage = storage or StorageService()
        self.providers = providers or ProviderRegistry()
        self.notifications = notifications or TelegramNotificationService()
        self.ledger = ledger or LedgerService()

    async def run(self, job_id: str) -> dict[str, str]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one()
            user_result = await session.execute(select(User).where(User.id == job.user_id))
            user = user_result.scalar_one()
            job.status = "running"
            await session.commit()

            try:
                input_result = await session.execute(select(JobInput).where(JobInput.job_id == job.id))
                job_input = input_result.scalar_one()
                input_bytes = self.storage.download_bytes(job_input.storage_key)

                provider = self.providers.get(job.provider or "remove_bg")
                provider_result = await provider.generate(
                    ImageGenerationRequest(
                        prompt=job.prompt_final,
                        source_assets=[job_input.public_url] if job_input.public_url else [],
                        references=[],
                        style_profile="transparent_product_cutout",
                        source_image_bytes=input_bytes,
                        mime_type=job_input.metadata_json.get("mime_type", "image/jpeg"),
                    )
                )

                sent_payload: bytes | None = None
                for idx, asset in enumerate(provider_result.assets):
                    result_key = f"users/{job.user_id}/jobs/{job.id}/results/result-{idx + 1}.png"
                    preview_url = asset.external_url
                    if asset.bytes_data:
                        self.storage.upload_bytes(result_key, asset.bytes_data, asset.mime_type)
                        preview_url = self.storage.public_url(result_key)
                        if sent_payload is None:
                            sent_payload = asset.bytes_data
                    session.add(
                        JobResult(
                            job_id=job.id,
                            variant_index=idx,
                            storage_key=result_key,
                            preview_url=preview_url,
                            width=asset.width,
                            height=asset.height,
                        )
                    )

                job.status = "succeeded"
                job.credits_charged = job.credits_reserved
                await session.commit()
                await self.ledger.commit_job_credits(
                    user_id=job.user_id,
                    job_id=job.id,
                    amount=job.credits_reserved,
                )

                if sent_payload is not None:
                    await self.notifications.send_remove_bg_result(
                        chat_id=user.telegram_user_id,
                        image_bytes=sent_payload,
                        caption=(
                            "Фон удалён в WHYNOT Photoshop.\n"
                            f"Job ID: `{job.id}`\n"
                            "Можешь использовать файл для маркетплейсов, дизайна и каталога."
                        ),
                        mime_type="image/png",
                    )
                return {"job_id": str(job.id), "status": job.status}
            except Exception:
                job.status = "failed"
                job.error_code = "job_runner_failed"
                await session.commit()
                await self.ledger.refund_job_credits(
                    user_id=job.user_id,
                    job_id=job.id,
                    amount=job.credits_reserved,
                )
                await self.notifications.send_job_failed(chat_id=user.telegram_user_id, job_id=str(job.id))
                raise
