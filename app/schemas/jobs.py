from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    mode: str = Field(min_length=2, max_length=64)
    prompt: str = Field(min_length=3, max_length=4000)
    template_code: str | None = Field(default=None, max_length=64)
    source_asset_keys: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    locale: str = Field(default="ru")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    credits_reserved: int
