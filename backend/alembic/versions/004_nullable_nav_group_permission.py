"""Make navigation_group_permissions.navigation_group_id nullable for 'all' access.

Revision ID: 004
Revises: 003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'navigation_group_permissions',
        'navigation_group_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    # Remove rows with NULL navigation_group_id before making NOT NULL
    op.execute("DELETE FROM navigation_group_permissions WHERE navigation_group_id IS NULL")
    op.alter_column(
        'navigation_group_permissions',
        'navigation_group_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
