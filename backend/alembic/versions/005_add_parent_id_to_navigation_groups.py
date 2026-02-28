"""Add parent_id to navigation_groups for 3-level submenu support.

Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'navigation_groups',
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('navigation_groups.id', ondelete='SET NULL'),
            nullable=True,
        )
    )
    op.create_index(
        'ix_navigation_groups_parent_id',
        'navigation_groups',
        ['parent_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_navigation_groups_parent_id', table_name='navigation_groups')
    op.drop_column('navigation_groups', 'parent_id')
