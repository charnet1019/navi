from sqlalchemy import Table, Column, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base
from app.utils.time import now_cst

# Many-to-many association tables

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime, default=now_cst, nullable=False),
    Column("assigned_by", UUID(as_uuid=True), ForeignKey("users.id")),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    Column("granted_at", DateTime, default=now_cst, nullable=False),
)

user_group_members = Table(
    "user_group_members",
    Base.metadata,
    Column("user_group_id", UUID(as_uuid=True), ForeignKey("user_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime, default=now_cst, nullable=False),
)


# Fine-grained permission models

class LinkPermission(Base):
    """Fine-grained link access permissions."""

    __tablename__ = "link_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("links.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user_group_id = Column(UUID(as_uuid=True), ForeignKey("user_groups.id", ondelete="CASCADE"))
    granted_at = Column(DateTime, default=now_cst, nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND user_group_id IS NULL) OR (user_id IS NULL AND user_group_id IS NOT NULL)",
            name="check_link_permission_target"
        ),
    )


user_favorites = Table(
    "user_favorites",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("link_id", UUID(as_uuid=True), ForeignKey("links.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=now_cst, nullable=False),
)


class NavigationGroupPermission(Base):
    """Fine-grained navigation group access permissions."""

    __tablename__ = "navigation_group_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    navigation_group_id = Column(UUID(as_uuid=True), ForeignKey("navigation_groups.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user_group_id = Column(UUID(as_uuid=True), ForeignKey("user_groups.id", ondelete="CASCADE"))
    granted_at = Column(DateTime, default=now_cst, nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND user_group_id IS NULL) OR (user_id IS NULL AND user_group_id IS NOT NULL)",
            name="check_nav_group_permission_target"
        ),
    )
