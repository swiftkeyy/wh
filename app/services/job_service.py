from uuid import uuid4

from sqlalchemy import select

from app.db.models import Job, JobInput, User
from app.db.session import AsyncSessionLocal
from app.tasks.image_jobs import process_image_job
from app.infra.storage import StorageService
from app.services.ledger import LedgerService
from app.services.pricing_policy import PricingPolicyService


class JobService:
    def __init__(
        self,
        storage: StorageService | None = None,
        ledger: LedgerService | None = None,
        pricing_policy: PricingPolicyService | None = None,
    ) -> None:
        self.storage = storage or StorageService()
        self.ledger = ledger or LedgerService()
        self.pricing_policy = pricing_policy or PricingPolicyService()

    async def create_remove_bg_job(
        self,
        telegram_user_id: int,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> str:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
            user = result.scalar_one()

            job = Job(
                user_id=user.id,
                job_type="remove_background",
                status="pending",
                provider="remove_bg",
                template_code="transparent_bg",
                prompt_final="Remove background from the uploaded image and keep clean subject edges.",
                prompt_version="system-1",
                credits_reserved=self.pricing_policy.get_job_price("transparent_bg"),
            )
            session.add(job)
            await session.flush()
            await self.ledger.reserve_job_credits(user_id=user.id, job_id=job.id, amount=job.credits_reserved)

            source_key = f"users/{user.id}/jobs/{job.id}/inputs/source-{uuid4().hex}.jpg"
            self.storage.upload_bytes(source_key, image_bytes, mime_type)
            session.add(
                JobInput(
                    job_id=job.id,
                    input_type="source_image",
                    storage_key=source_key,
                    public_url=self.storage.public_url(source_key),
                    metadata_json={"mime_type": mime_type},
                )
            )
            await session.commit()

        process_image_job.delay(str(job.id))
        return str(job.id)
