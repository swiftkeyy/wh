from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TemplateTier(StrEnum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"
