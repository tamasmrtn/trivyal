"""Add patchrequest and restartrequest tables for Copa remediation.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-21

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = {row[0] for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))}

    if "patchrequest" in existing:
        return

    op.create_table(
        "patchrequest",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("agent.id"), nullable=False),
        sa.Column("container_id", sa.String(), sa.ForeignKey("container.id"), nullable=False),
        sa.Column("image_name", sa.String(), nullable=False),
        sa.Column("patched_tag", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("original_finding_count", sa.Integer(), nullable=True),
        sa.Column("patched_finding_count", sa.Integer(), nullable=True),
        sa.Column("log_lines", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_patchrequest_agent_id", "patchrequest", ["agent_id"])
    op.create_index("ix_patchrequest_container_id", "patchrequest", ["container_id"])

    op.create_table(
        "restartrequest",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patch_request_id", sa.String(), sa.ForeignKey("patchrequest.id"), nullable=False),
        sa.Column("container_id", sa.String(), sa.ForeignKey("container.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("block_reason", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("reverted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_restartrequest_patch_request_id", "restartrequest", ["patch_request_id"])
    op.create_index("ix_restartrequest_container_id", "restartrequest", ["container_id"])


def downgrade() -> None:
    op.drop_table("restartrequest")
    op.drop_table("patchrequest")
