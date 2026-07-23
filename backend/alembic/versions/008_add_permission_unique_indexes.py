"""add unique indexes for fine grained permissions

Revision ID: 008
Revises: 007
Create Date: 2026-07-22

"""
from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_link_permissions_link_user",
        "link_permissions",
        ["link_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_link_permissions_link_user_group",
        "link_permissions",
        ["link_id", "user_group_id"],
        unique=True,
        postgresql_where=sa.text("user_group_id IS NOT NULL"),
    )
    op.create_index(
        "uq_nav_group_permissions_group_user",
        "navigation_group_permissions",
        ["navigation_group_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("navigation_group_id IS NOT NULL AND user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_nav_group_permissions_group_user_group",
        "navigation_group_permissions",
        ["navigation_group_id", "user_group_id"],
        unique=True,
        postgresql_where=sa.text("navigation_group_id IS NOT NULL AND user_group_id IS NOT NULL"),
    )
    op.create_index(
        "uq_nav_group_permissions_all_user",
        "navigation_group_permissions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("navigation_group_id IS NULL AND user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_nav_group_permissions_all_user_group",
        "navigation_group_permissions",
        ["user_group_id"],
        unique=True,
        postgresql_where=sa.text("navigation_group_id IS NULL AND user_group_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_nav_group_permissions_all_user_group", table_name="navigation_group_permissions")
    op.drop_index("uq_nav_group_permissions_all_user", table_name="navigation_group_permissions")
    op.drop_index("uq_nav_group_permissions_group_user_group", table_name="navigation_group_permissions")
    op.drop_index("uq_nav_group_permissions_group_user", table_name="navigation_group_permissions")
    op.drop_index("uq_link_permissions_link_user_group", table_name="link_permissions")
    op.drop_index("uq_link_permissions_link_user", table_name="link_permissions")
