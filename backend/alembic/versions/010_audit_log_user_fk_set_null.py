"""set audit_logs.user_id FK to ON DELETE SET NULL

Revision ID: 010
Revises: 009
Create Date: 2026-07-22

Audit rows must outlive the user that generated them (that's the whole
point of an audit trail), but the original FK had no ON DELETE clause,
so deleting a user who had ever triggered an audited action would fail
with a FK violation. SET NULL keeps the historical row while dropping
the now-dangling reference.
"""
from alembic import op


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "audit_logs_user_id_fkey",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "audit_logs_user_id_fkey",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
    )
