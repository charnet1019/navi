from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base
from app.utils.time import now_cst


class SystemSetting(Base):
    """System settings model for global configuration."""

    __tablename__ = "system_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=now_cst, onupdate=now_cst, nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
