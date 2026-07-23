"""add audit log retention setting

Revision ID: 011
Revises: 010
Create Date: 2026-07-23
"""
import uuid

from alembic import op
import sqlalchemy as sa


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO system_settings (id, key, value, description, updated_at)
            VALUES (:id, :key, :value, :description, now())
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "key": "audit_log_retention_days",
            "value": "30",
            "description": "Number of days to retain audit logs",
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM system_settings WHERE key = :key"),
        {"key": "audit_log_retention_days"},
    )
