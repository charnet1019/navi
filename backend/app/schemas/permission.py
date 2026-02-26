"""Permission-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """Base permission schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    id: UUID
    name: str
    resource: str
    action: str
    description: str | None

    model_config = {"from_attributes": True}


class GrantPermissionRequest(BaseModel):
    """Schema for granting a fine-grained permission."""
    user_id: UUID | None = None
    user_group_id: UUID | None = None


class NavGroupPermissionResponse(BaseModel):
    """Schema for navigation group permission listing."""
    id: UUID
    navigation_group_id: UUID | None
    user_id: UUID | None
    user_group_id: UUID | None
    user_name: str | None = None
    user_group_name: str | None = None
    granted_at: datetime
    granted_by: UUID | None


class LinkPermissionResponse(BaseModel):
    """Schema for link permission listing."""
    id: UUID
    link_id: UUID
    user_id: UUID | None
    user_group_id: UUID | None
    user_name: str | None = None
    user_group_name: str | None = None
    granted_at: datetime
    granted_by: UUID | None
