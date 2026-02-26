from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base
from app.utils.time import now_cst


class Link(Base):
    """Link model for service links."""

    __tablename__ = "links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    icon_path = Column(String(255))
    navigation_group_id = Column(UUID(as_uuid=True), ForeignKey("navigation_groups.id"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    open_in_new_tab = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=now_cst, nullable=False)
    updated_at = Column(DateTime, default=now_cst, onupdate=now_cst, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_links")
    navigation_group = relationship("NavigationGroup", back_populates="links")
