"""add report batch id

Revision ID: 0002_add_report_batch_id
Revises: 0001_initial
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_report_batch_id"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_reports_batch_id"), "reports", ["batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_batch_id"), table_name="reports")
    op.drop_column("reports", "batch_id")
