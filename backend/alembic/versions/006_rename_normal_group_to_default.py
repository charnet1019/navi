"""Rename user group 'normal' to 'default'

Revision ID: 006
Revises: 005
Create Date: 2026-02-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE user_groups SET name = 'default' WHERE name = 'normal'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE user_groups SET name = 'normal' WHERE name = 'default'"))
