"""initial schema

Revision ID: 20260409_0001
Revises:
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260409_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("language_code", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column("acquisition_channel", sa.String(length=64), nullable=True),
        sa.Column("referral_code", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_user_id"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_acquisition_channel", "users", ["acquisition_channel"])

    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="ru-RU"),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("persona_segment", sa.String(length=64), nullable=True),
        sa.Column("first_value_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pending_mode", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])
    op.create_index("ix_user_profiles_persona_segment", "user_profiles", ["persona_segment"])
    op.create_index("ix_user_profiles_pending_mode", "user_profiles", ["pending_mode"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("renews_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_plan_code", "subscriptions", ["plan_code"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_renews_at", "subscriptions", ["renews_at"])

    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("purchase_type", sa.String(length=24), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"])
    op.create_index("ix_purchases_purchase_type", "purchases", ["purchase_type"])
    op.create_index("ix_purchases_sku", "purchases", ["sku"])
    op.create_index("ix_purchases_status", "purchases", ["status"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("template_code", sa.String(length=64), nullable=True),
        sa.Column("queue_name", sa.String(length=32), nullable=False, server_default="image_jobs"),
        sa.Column("prompt_final", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("credits_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credits_charged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_provider", "jobs", ["provider"])
    op.create_index("ix_jobs_template_code", "jobs", ["template_code"])
    op.create_index("ix_jobs_error_code", "jobs", ["error_code"])
    op.create_index("ix_jobs_started_at", "jobs", ["started_at"])
    op.create_index("ix_jobs_finished_at", "jobs", ["finished_at"])
    op.create_index("ix_jobs_user_status_created", "jobs", ["user_id", "status", "created_at"])
    op.create_index("ix_jobs_template_created", "jobs", ["template_code", "created_at"])

    op.create_table(
        "credit_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id"), nullable=True),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_credit_ledger_user_id", "credit_ledger", ["user_id"])
    op.create_index("ix_credit_ledger_direction", "credit_ledger", ["direction"])
    op.create_index("ix_credit_ledger_reason", "credit_ledger", ["reason"])
    op.create_index("ix_credit_ledger_job_id", "credit_ledger", ["job_id"])
    op.create_index("ix_credit_ledger_purchase_id", "credit_ledger", ["purchase_id"])

    op.create_table(
        "job_inputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("input_type", sa.String(length=24), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("public_url", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_job_inputs_job_id", "job_inputs", ["job_id"])
    op.create_index("ix_job_inputs_input_type", "job_inputs", ["input_type"])

    op.create_table(
        "job_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("variant_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("preview_url", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("watermark_applied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_job_results_job_id", "job_results", ["job_id"])

    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("tier", sa.String(length=16), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_prompt_templates_category", "prompt_templates", ["category"])
    op.create_index("ix_prompt_templates_status", "prompt_templates", ["status"])
    op.create_index("ix_prompt_templates_tier", "prompt_templates", ["tier"])
    op.create_index("ix_prompt_templates_is_featured", "prompt_templates", ["is_featured"])

    op.create_table(
        "prompt_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_templates.id"), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("moderation_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("ab_bucket", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("template_id", "version", "locale", name="uq_template_version_locale"),
    )
    op.create_index("ix_prompt_template_versions_template_id", "prompt_template_versions", ["template_id"])
    op.create_index("ix_prompt_template_versions_locale", "prompt_template_versions", ["locale"])
    op.create_index("ix_prompt_template_versions_ab_bucket", "prompt_template_versions", ["ab_bucket"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider_payment_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_payments_purchase_id", "payments", ["purchase_id"])
    op.create_index("ix_payments_provider", "payments", ["provider"])
    op.create_index("ix_payments_status", "payments", ["status"])

    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("inviter_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("invited_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("reward_granted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("invited_user_id"),
    )
    op.create_index("ix_referrals_inviter_user_id", "referrals", ["inviter_user_id"])
    op.create_index("ix_referrals_status", "referrals", ["status"])
    op.create_index("ix_referrals_reward_granted", "referrals", ["reward_granted"])

    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("flag_key", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("flag_key"),
    )
    op.create_index("ix_feature_flags_enabled", "feature_flags", ["enabled"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_type", sa.String(length=24), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("subject_type", sa.String(length=64), nullable=True),
        sa.Column("subject_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_actor_type", "audit_logs", ["actor_type"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_subject_type", "audit_logs", ["subject_type"])
    op.create_index("ix_audit_logs_subject_id", "audit_logs", ["subject_id"])

    op.create_table(
        "admin_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_admin_actions_admin_user_id", "admin_actions", ["admin_user_id"])
    op.create_index("ix_admin_actions_action_type", "admin_actions", ["action_type"])
    op.create_index("ix_admin_actions_target_type", "admin_actions", ["target_type"])
    op.create_index("ix_admin_actions_target_id", "admin_actions", ["target_id"])

    op.create_table(
        "support_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_job_id", "support_tickets", ["job_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_support_tickets_category", "support_tickets", ["category"])

    op.create_table(
        "banned_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_banned_users_source", "banned_users", ["source"])
    op.create_index("ix_banned_users_expires_at", "banned_users", ["expires_at"])


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_banned_users_expires_at", "banned_users"),
        ("ix_banned_users_source", "banned_users"),
        ("ix_support_tickets_category", "support_tickets"),
        ("ix_support_tickets_status", "support_tickets"),
        ("ix_support_tickets_job_id", "support_tickets"),
        ("ix_support_tickets_user_id", "support_tickets"),
        ("ix_admin_actions_target_id", "admin_actions"),
        ("ix_admin_actions_target_type", "admin_actions"),
        ("ix_admin_actions_action_type", "admin_actions"),
        ("ix_admin_actions_admin_user_id", "admin_actions"),
        ("ix_audit_logs_subject_id", "audit_logs"),
        ("ix_audit_logs_subject_type", "audit_logs"),
        ("ix_audit_logs_action", "audit_logs"),
        ("ix_audit_logs_actor_id", "audit_logs"),
        ("ix_audit_logs_actor_type", "audit_logs"),
        ("ix_feature_flags_enabled", "feature_flags"),
        ("ix_referrals_reward_granted", "referrals"),
        ("ix_referrals_status", "referrals"),
        ("ix_referrals_inviter_user_id", "referrals"),
        ("ix_payments_status", "payments"),
        ("ix_payments_provider", "payments"),
        ("ix_payments_purchase_id", "payments"),
        ("ix_prompt_template_versions_ab_bucket", "prompt_template_versions"),
        ("ix_prompt_template_versions_locale", "prompt_template_versions"),
        ("ix_prompt_template_versions_template_id", "prompt_template_versions"),
        ("ix_prompt_templates_is_featured", "prompt_templates"),
        ("ix_prompt_templates_tier", "prompt_templates"),
        ("ix_prompt_templates_status", "prompt_templates"),
        ("ix_prompt_templates_category", "prompt_templates"),
        ("ix_job_results_job_id", "job_results"),
        ("ix_job_inputs_input_type", "job_inputs"),
        ("ix_job_inputs_job_id", "job_inputs"),
        ("ix_credit_ledger_purchase_id", "credit_ledger"),
        ("ix_credit_ledger_job_id", "credit_ledger"),
        ("ix_credit_ledger_reason", "credit_ledger"),
        ("ix_credit_ledger_direction", "credit_ledger"),
        ("ix_credit_ledger_user_id", "credit_ledger"),
        ("ix_jobs_template_created", "jobs"),
        ("ix_jobs_user_status_created", "jobs"),
        ("ix_jobs_finished_at", "jobs"),
        ("ix_jobs_started_at", "jobs"),
        ("ix_jobs_error_code", "jobs"),
        ("ix_jobs_template_code", "jobs"),
        ("ix_jobs_provider", "jobs"),
        ("ix_jobs_status", "jobs"),
        ("ix_jobs_job_type", "jobs"),
        ("ix_jobs_user_id", "jobs"),
        ("ix_purchases_status", "purchases"),
        ("ix_purchases_sku", "purchases"),
        ("ix_purchases_purchase_type", "purchases"),
        ("ix_purchases_user_id", "purchases"),
        ("ix_subscriptions_renews_at", "subscriptions"),
        ("ix_subscriptions_status", "subscriptions"),
        ("ix_subscriptions_plan_code", "subscriptions"),
        ("ix_subscriptions_user_id", "subscriptions"),
        ("ix_user_profiles_pending_mode", "user_profiles"),
        ("ix_user_profiles_persona_segment", "user_profiles"),
        ("ix_user_profiles_user_id", "user_profiles"),
        ("ix_users_acquisition_channel", "users"),
        ("ix_users_is_active", "users"),
        ("ix_users_username", "users"),
        ("ix_users_telegram_user_id", "users"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "banned_users",
        "support_tickets",
        "admin_actions",
        "audit_logs",
        "feature_flags",
        "referrals",
        "payments",
        "prompt_template_versions",
        "prompt_templates",
        "job_results",
        "job_inputs",
        "credit_ledger",
        "jobs",
        "purchases",
        "subscriptions",
        "user_profiles",
        "users",
    ]:
        op.drop_table(table_name)
