"""Add MisconfigFinding table, Container.image_tag, and RiskAcceptance.misconfig_finding_id.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    result = conn.scalar(
        sa.text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table},
    )
    return bool(result)


def upgrade() -> None:
    # Add image_tag to container (skip if already present from metadata.create_all)
    if not _column_exists("container", "image_tag"):
        op.add_column("container", sa.Column("image_tag", sa.VARCHAR(), nullable=True))

    # Create misconfigfinding table
    if not _table_exists("misconfigfinding"):
        op.create_table(
            "misconfigfinding",
            sa.Column("id", sa.VARCHAR(), nullable=False),
            sa.Column("container_id", sa.VARCHAR(), nullable=False),
            sa.Column("check_id", sa.VARCHAR(), nullable=False),
            sa.Column("severity", sa.VARCHAR(), nullable=False),
            sa.Column("title", sa.VARCHAR(), nullable=False),
            sa.Column("fix_guideline", sa.VARCHAR(), nullable=False),
            sa.Column("status", sa.VARCHAR(), nullable=False),
            sa.Column("first_seen", sa.DateTime(), nullable=False),
            sa.Column("last_seen", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["container_id"], ["container.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_misconfigfinding_container_id", "misconfigfinding", ["container_id"])
        op.create_index("ix_misconfigfinding_check_id", "misconfigfinding", ["check_id"])

    # Extend riskacceptance: make finding_id nullable, add misconfig_finding_id
    if not _column_exists("riskacceptance", "misconfig_finding_id"):
        with op.batch_alter_table("riskacceptance") as batch_op:
            batch_op.alter_column("finding_id", existing_type=sa.VARCHAR(), nullable=True)
            batch_op.add_column(sa.Column("misconfig_finding_id", sa.VARCHAR(), nullable=True))
            batch_op.create_foreign_key(
                "fk_riskacceptance_misconfig_finding_id",
                "misconfigfinding",
                ["misconfig_finding_id"],
                ["id"],
            )
            batch_op.create_index(
                "ix_riskacceptance_misconfig_finding_id",
                ["misconfig_finding_id"],
            )

    # Backfill image_tag from image_name where it contains ':'
    op.execute(
        "UPDATE container SET image_tag = SUBSTR(image_name, INSTR(image_name, ':') + 1) "
        "WHERE image_name LIKE '%:%' AND (image_tag IS NULL OR image_tag = '')"
    )
    op.execute(
        "UPDATE container SET image_name = SUBSTR(image_name, 1, INSTR(image_name, ':') - 1) "
        "WHERE image_name LIKE '%:%'"
    )


def downgrade() -> None:
    pass
