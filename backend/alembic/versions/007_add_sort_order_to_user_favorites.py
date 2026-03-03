"""add sort_order to user_favorites

Revision ID: 007
Revises: 006
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('user_favorites', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('user_favorites', 'sort_order')
