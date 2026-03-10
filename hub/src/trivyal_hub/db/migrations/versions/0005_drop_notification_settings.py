"""Drop notificationsettings table — notification feature removed.

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-10

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notificationsettings")


def downgrade() -> None:
    pass
