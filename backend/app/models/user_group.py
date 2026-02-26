from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base
from app.utils.time import now_cst


class UserGroup(Base):
    """User group model for organizing users."""

    __tablename__ = "user_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=now_cst, nullable=False)
    updated_at = Column(DateTime, default=now_cst, onupdate=now_cst, nullable=False)

    # Relationships
    members = relationship("User", secondary="user_group_members", back_populates="user_groups")
