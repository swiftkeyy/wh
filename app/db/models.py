import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    language_code: Mapped[str] = mapped_column(String(8), default="ru")
    acquisition_channel: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    referral_code: Mapped[Optional[str]] = mapped_column(String(32), unique=True)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64))
    locale: Mapped[str] = mapped_column(String(16), default="ru-RU")
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    persona_segment: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    first_value_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pending_mode: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    user: Mapped["User"] = relationship(back_populates="profile")


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    plan_code: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    renews_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str] = mapped_column(String(24))


class CreditLedger(TimestampMixin, Base):
    __tablename__ = "credit_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    direction: Mapped[str] = mapped_column(String(8), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64), index=True)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("jobs.id"), index=True)
    purchase_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("purchases.id"), index=True)
    balance_after: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    entry_status: Mapped[str] = mapped_column(String(16), default="posted", index=True)


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    job_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    template_code: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    queue_name: Mapped[str] = mapped_column(String(32), default="image_jobs")
    prompt_final: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(32))
    credits_reserved: Mapped[int] = mapped_column(Integer, default=0)
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index("ix_jobs_user_status_created", "user_id", "status", "created_at"),
        Index("ix_jobs_template_created", "template_code", "created_at"),
    )


class JobInput(TimestampMixin, Base):
    __tablename__ = "job_inputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    input_type: Mapped[str] = mapped_column(String(24), index=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(255))
    public_url: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)


class JobResult(TimestampMixin, Base):
    __tablename__ = "job_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    variant_index: Mapped[int] = mapped_column(Integer, default=0)
    storage_key: Mapped[str] = mapped_column(String(255))
    preview_url: Mapped[Optional[str]] = mapped_column(Text)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    watermark_applied: Mapped[bool] = mapped_column(Boolean, default=False)


class PromptTemplate(TimestampMixin, Base):
    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    tier: Mapped[str] = mapped_column(String(16), index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)


class PromptTemplateVersion(TimestampMixin, Base):
    __tablename__ = "prompt_template_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompt_templates.id"), index=True)
    version: Mapped[str] = mapped_column(String(32))
    locale: Mapped[str] = mapped_column(String(8), default="ru", index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(Text)
    prompt_schema: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"))
    moderation_tags: Mapped[list] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    ab_bucket: Mapped[Optional[str]] = mapped_column(String(32), index=True)

    __table_args__ = (UniqueConstraint("template_id", "version", "locale", name="uq_template_version_locale"),)


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    purchase_type: Mapped[str] = mapped_column(String(24), index=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("purchases.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    provider_payment_id: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)


class Referral(TimestampMixin, Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inviter_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    invited_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class FeatureFlag(TimestampMixin, Base):
    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_key: Mapped[str] = mapped_column(String(128), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_type: Mapped[str] = mapped_column(String(24), index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    subject_type: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)


class AdminAction(TimestampMixin, Base):
    __tablename__ = "admin_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[str] = mapped_column(String(128), index=True)
    note: Mapped[Optional[str]] = mapped_column(Text)


class SupportTicket(TimestampMixin, Base):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text)


class BannedUser(TimestampMixin, Base):
    __tablename__ = "banned_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    reason: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(32), index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
