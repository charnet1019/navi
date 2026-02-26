"""System setting-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SystemSettingBase(BaseModel):
    """Base system setting schema with common fields."""
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1)
    description: Optional[str] = None


class SystemSettingUpdate(BaseModel):
    """Schema for updating an existing system setting."""
    value: str = Field(...)


class SystemSettingResponse(BaseModel):
    """Schema for system setting response."""
    id: UUID
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime
    updated_by: Optional[UUID]

    model_config = {"from_attributes": True}
