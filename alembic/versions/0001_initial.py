"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM("admin", "user", name="user_role", create_type=False)
    resource_type = postgresql.ENUM(
        "okrug_community",
        "district_community",
        "lom_personal",
        "other",
        name="resource_type",
        create_type=False,
    )
    report_status = postgresql.ENUM(
        "pending", "running", "done", "failed", name="report_status", create_type=False
    )
    user_role.create(op.get_bind(), checkfirst=True)
    resource_type.create(op.get_bind(), checkfirst=True)
    report_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "networks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["network_id"], ["networks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
    )
    op.create_index(op.f("ix_users_login"), "users", ["login"], unique=False)

    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vk_owner_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_screen_name", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("resource_type", resource_type, nullable=False),
        sa.Column("category_label", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["network_id"], ["networks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("network_id", "vk_owner_id", name="uq_resource_network_owner"),
    )
    op.create_index(op.f("ix_resources_network_id"), "resources", ["network_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_owner_id", sa.BigInteger(), nullable=False),
        sa.Column("source_post_id", sa.BigInteger(), nullable=False),
        sa.Column("source_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("infopovod_title", sa.String(length=512), nullable=False),
        sa.Column("status", report_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["network_id"], ["networks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_created_by"), "reports", ["created_by"], unique=False)
    op.create_index(op.f("ix_reports_network_id"), "reports", ["network_id"], unique=False)

    op.create_table(
        "report_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repost_owner_id", sa.BigInteger(), nullable=False),
        sa.Column("repost_post_id", sa.BigInteger(), nullable=False),
        sa.Column("repost_url", sa.Text(), nullable=False),
        sa.Column("repost_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("followers_count", sa.Integer(), nullable=False),
        sa.Column("views_count", sa.Integer(), nullable=True),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_rows_report_id"), "report_rows", ["report_id"], unique=False)
    op.create_index(op.f("ix_report_rows_resource_id"), "report_rows", ["resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_rows_resource_id"), table_name="report_rows")
    op.drop_index(op.f("ix_report_rows_report_id"), table_name="report_rows")
    op.drop_table("report_rows")
    op.drop_index(op.f("ix_reports_network_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_created_by"), table_name="reports")
    op.drop_table("reports")
    op.drop_index(op.f("ix_resources_network_id"), table_name="resources")
    op.drop_table("resources")
    op.drop_index(op.f("ix_users_login"), table_name="users")
    op.drop_table("users")
    op.drop_table("networks")
    postgresql.ENUM(name="report_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="resource_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
