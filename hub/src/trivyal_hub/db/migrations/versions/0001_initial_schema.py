"""Initial schema — all tables from the pre-Alembic baseline.

Revision ID: 0001
Revises: None
Create Date: 2026-03-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hubsettings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_key", sa.VARCHAR(), nullable=False),
        sa.Column("private_key", sa.VARCHAR(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=False),
        sa.Column("token_hash", sa.VARCHAR(), nullable=False),
        sa.Column("fingerprint", sa.VARCHAR(), nullable=True),
        sa.Column("status", sa.VARCHAR(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("host_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_agent_name", "agent", ["name"])
    op.create_table(
        "notificationsettings",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("webhook_url", sa.VARCHAR(), nullable=True),
        sa.Column("webhook_type", sa.VARCHAR(), nullable=True),
        sa.Column("notify_on_critical", sa.Boolean(), nullable=False),
        sa.Column("notify_on_high", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "container",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("agent_id", sa.VARCHAR(), nullable=False),
        sa.Column("image_name", sa.VARCHAR(), nullable=False),
        sa.Column("container_name", sa.VARCHAR(), nullable=True),
        sa.Column("image_digest", sa.VARCHAR(), nullable=True),
        sa.Column("last_scanned", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_container_agent_id", "container", ["agent_id"])
    op.create_table(
        "scanresult",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("container_id", sa.VARCHAR(), nullable=False),
        sa.Column("agent_id", sa.VARCHAR(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(), nullable=False),
        sa.Column("trivy_raw", sa.JSON(), nullable=True),
        sa.Column("critical_count", sa.Integer(), nullable=False),
        sa.Column("high_count", sa.Integer(), nullable=False),
        sa.Column("medium_count", sa.Integer(), nullable=False),
        sa.Column("low_count", sa.Integer(), nullable=False),
        sa.Column("unknown_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"]),
        sa.ForeignKeyConstraint(["container_id"], ["container.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scanresult_agent_id", "scanresult", ["agent_id"])
    op.create_index("ix_scanresult_container_id", "scanresult", ["container_id"])
    op.create_table(
        "finding",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("scan_result_id", sa.VARCHAR(), nullable=False),
        sa.Column("cve_id", sa.VARCHAR(), nullable=False),
        sa.Column("package_name", sa.VARCHAR(), nullable=False),
        sa.Column("installed_version", sa.VARCHAR(), nullable=False),
        sa.Column("fixed_version", sa.VARCHAR(), nullable=True),
        sa.Column("severity", sa.VARCHAR(), nullable=False),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("status", sa.VARCHAR(), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_result_id"], ["scanresult.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finding_cve_id", "finding", ["cve_id"])
    op.create_index("ix_finding_scan_result_id", "finding", ["scan_result_id"])
    op.create_table(
        "riskacceptance",
        sa.Column("id", sa.VARCHAR(), nullable=False),
        sa.Column("finding_id", sa.VARCHAR(), nullable=False),
        sa.Column("reason", sa.VARCHAR(), nullable=False),
        sa.Column("accepted_by", sa.VARCHAR(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["finding_id"], ["finding.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_riskacceptance_finding_id", "riskacceptance", ["finding_id"])


def downgrade() -> None:
    pass
