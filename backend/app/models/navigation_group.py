from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
import uuid

from app.database import Base
from app.utils.time import now_cst


class NavigationGroup(Base):
    """Navigation group model for sidebar organization."""

    __tablename__ = "navigation_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(255))
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("navigation_groups.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=now_cst, nullable=False)
    updated_at = Column(DateTime, default=now_cst, onupdate=now_cst, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_navigation_groups")
    links = relationship("Link", back_populates="navigation_group", cascade="all, delete-orphan")
    children = relationship(
        "NavigationGroup",
        backref=backref("parent", remote_side=[id]),
        foreign_keys=[parent_id],
        order_by="NavigationGroup.sort_order",
    )
