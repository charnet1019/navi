"""Add default user groups (admin, normal) and assign existing users

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert default user groups and assign existing users."""
    conn = op.get_bind()

    admin_group_id = str(uuid.uuid4())
    normal_group_id = str(uuid.uuid4())

    # Create default user groups
    conn.execute(
        sa.text("""
            INSERT INTO user_groups (id, name, description, created_at, updated_at)
            VALUES
                (:admin_id, 'admin', 'Superuser group with full access', now(), now()),
                (:normal_id, 'normal', 'Regular users with standard access', now(), now())
        """),
        {'admin_id': admin_group_id, 'normal_id': normal_group_id}
    )

    # Assign existing superusers to admin group
    conn.execute(
        sa.text("""
            INSERT INTO user_group_members (user_group_id, user_id, joined_at)
            SELECT :admin_group_id, id, now()
            FROM users
            WHERE is_superuser = true
        """),
        {'admin_group_id': admin_group_id}
    )

    # Assign existing non-superusers to normal group
    conn.execute(
        sa.text("""
            INSERT INTO user_group_members (user_group_id, user_id, joined_at)
            SELECT :normal_group_id, id, now()
            FROM users
            WHERE is_superuser = false
        """),
        {'normal_group_id': normal_group_id}
    )


def downgrade() -> None:
    """Remove default user groups."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM user_groups WHERE name IN ('admin', 'normal')")
    )
