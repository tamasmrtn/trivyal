"""Change container identity key from (agent_id, image_name, image_tag, container_name)
to (agent_id, container_name, image_name), dropping image_tag from uniqueness.

This means a rebuilt container (same name, new image tag) reuses the existing
Container row instead of creating a new one, so findings are correctly
deduplicated across rebuilds.

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-09

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Keep the oldest row per new natural key (agent_id, container_name, image_name).
_KEEP = "SELECT MIN(id) FROM container GROUP BY agent_id, container_name, image_name"


def upgrade() -> None:
    # --- Step 1: cascade-delete orphaned child rows ---------------------------
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

    # --- Step 3: replace the UNIQUE constraint --------------------------------
    with op.batch_alter_table("container") as batch_op:
        batch_op.drop_constraint("uq_container_agent_image", type_="unique")
        batch_op.create_unique_constraint(
            "uq_container_agent_image",
            ["agent_id", "container_name", "image_name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("container") as batch_op:
        batch_op.drop_constraint("uq_container_agent_image", type_="unique")
        batch_op.create_unique_constraint(
            "uq_container_agent_image",
            ["agent_id", "image_name", "image_tag", "container_name"],
        )
