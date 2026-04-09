from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, job_id) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def list_recent_for_user(self, user_id, limit: int = 20) -> list[Job]:
        result = await self.session.execute(
            select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc()).limit(limit)
        )
        return list(result.scalars())
