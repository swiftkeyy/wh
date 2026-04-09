"""add credit ledger entry status

Revision ID: 20260409_0002
Revises: 20260409_0001
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260409_0002"
down_revision = "20260409_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "credit_ledger",
        sa.Column("entry_status", sa.String(length=16), nullable=False, server_default="posted"),
    )
    op.create_index("ix_credit_ledger_entry_status", "credit_ledger", ["entry_status"])


def downgrade() -> None:
    op.drop_index("ix_credit_ledger_entry_status", table_name="credit_ledger")
    op.drop_column("credit_ledger", "entry_status")
