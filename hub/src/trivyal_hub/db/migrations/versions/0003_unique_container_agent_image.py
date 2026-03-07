"""Deduplicate container rows and enforce unique (agent_id, image_name, image_tag, container_name).

Migration 0002 backfilled image_name by stripping tags, which can collapse
rows that previously had distinct full names (e.g. nginx:1.25 and nginx:1.26)
into duplicates with the same (agent_id, image_name, image_tag, container_name).
This migration removes those duplicates (keeping the oldest row per group) and
adds the UNIQUE constraint that should have been there from the start.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-07

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Subquery that selects the one container id to KEEP per natural key.
# MIN(id) gives a deterministic choice among UUID hex strings.
_KEEP = "SELECT MIN(id) FROM container GROUP BY agent_id, image_name, image_tag, container_name"


def upgrade() -> None:
    # --- Step 1: cascade-delete orphaned child rows ---------------------------
    # SQLite does not enforce FK constraints unless PRAGMA foreign_keys = ON,
    # so we handle the cascade manually in the correct dependency order.

    op.execute(
        "DELETE FROM riskacceptance "  # nosec B608
        "WHERE finding_id IN ("
        "  SELECT f.id FROM finding f"
        "  JOIN scanresult sr ON f.scan_result_id = sr.id"
        f" WHERE sr.container_id NOT IN ({_KEEP})"
        ")"
    )
    op.execute(
        f"DELETE FROM finding WHERE scan_result_id IN ("  # nosec B608
        f"  SELECT id FROM scanresult WHERE container_id NOT IN ({_KEEP}))"
    )
    op.execute(f"DELETE FROM scanresult WHERE container_id NOT IN ({_KEEP})")  # nosec B608

    op.execute(
        "DELETE FROM riskacceptance "  # nosec B608
        "WHERE misconfig_finding_id IN ("
        "  SELECT id FROM misconfigfinding"
        f" WHERE container_id NOT IN ({_KEEP})"
        ")"
    )
    op.execute(f"DELETE FROM misconfigfinding WHERE container_id NOT IN ({_KEEP})")  # nosec B608

    # --- Step 2: remove duplicate container rows ------------------------------
    op.execute(f"DELETE FROM container WHERE id NOT IN ({_KEEP})")  # nosec B608

    # --- Step 3: add the UNIQUE constraint ------------------------------------
    with op.batch_alter_table("container") as batch_op:
        batch_op.create_unique_constraint(
            "uq_container_agent_image",
            ["agent_id", "image_name", "image_tag", "container_name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("container") as batch_op:
        batch_op.drop_constraint("uq_container_agent_image", type_="unique")
