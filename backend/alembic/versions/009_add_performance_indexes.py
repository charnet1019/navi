"""add indexes on frequently filtered foreign key / status columns

Revision ID: 009
Revises: 008
Create Date: 2026-07-22

"""
from alembic import op


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_links_navigation_group_id", "links", ["navigation_group_id"])
    op.create_index("ix_links_is_active", "links", ["is_active"])
    op.create_index("ix_link_permissions_link_id", "link_permissions", ["link_id"])
    op.create_index("ix_link_permissions_user_id", "link_permissions", ["user_id"])
    op.create_index("ix_link_permissions_user_group_id", "link_permissions", ["user_group_id"])
    op.create_index(
        "ix_navigation_group_permissions_navigation_group_id",
        "navigation_group_permissions",
        ["navigation_group_id"],
    )
    op.create_index("ix_navigation_group_permissions_user_id", "navigation_group_permissions", ["user_id"])
    op.create_index(
        "ix_navigation_group_permissions_user_group_id",
        "navigation_group_permissions",
        ["user_group_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_navigation_group_permissions_user_group_id", table_name="navigation_group_permissions")
    op.drop_index("ix_navigation_group_permissions_user_id", table_name="navigation_group_permissions")
    op.drop_index("ix_navigation_group_permissions_navigation_group_id", table_name="navigation_group_permissions")
    op.drop_index("ix_link_permissions_user_group_id", table_name="link_permissions")
    op.drop_index("ix_link_permissions_user_id", table_name="link_permissions")
    op.drop_index("ix_link_permissions_link_id", table_name="link_permissions")
    op.drop_index("ix_links_is_active", table_name="links")
    op.drop_index("ix_links_navigation_group_id", table_name="links")
