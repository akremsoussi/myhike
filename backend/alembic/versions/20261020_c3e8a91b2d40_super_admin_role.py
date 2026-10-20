"""super admin role

Revision ID: c3e8a91b2d40
Revises: b1d7072b9686
Create Date: 2026-10-20 11:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e8a91b2d40"
down_revision: str | Sequence[str] | None = "b1d7072b9686"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "role",
        existing_type=sa.Enum("user", "moderator", name="role"),
        type_=sa.Enum("user", "moderator", "super_admin", name="role"),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE users SET role = 'moderator' WHERE role = 'super_admin'")
    op.alter_column(
        "users",
        "role",
        existing_type=sa.Enum("user", "moderator", "super_admin", name="role"),
        type_=sa.Enum("user", "moderator", name="role"),
        existing_nullable=False,
    )

