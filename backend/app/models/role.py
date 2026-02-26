from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base
from app.utils.time import now_cst


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now_cst, nullable=False)
    updated_at = Column(DateTime, default=now_cst, onupdate=now_cst, nullable=False)

    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id",
    )
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
