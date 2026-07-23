"""Audit log-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Schema for audit log entry response."""
    id: UUID
    user_id: Optional[UUID]
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    changes: Optional[dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
