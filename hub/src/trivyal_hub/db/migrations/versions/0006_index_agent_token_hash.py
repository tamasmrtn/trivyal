"""Add index on agent.token_hash for O(1) auth lookup.

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-12

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_agent_token_hash", "agent", ["token_hash"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_agent_token_hash", "agent")
