"""Role-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.permission import PermissionResponse


class RoleBase(BaseModel):
    """Base role schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class RoleResponse(BaseModel):
    """Schema for role response."""
    id: UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleWithPermissions(RoleResponse):
    """Schema for role response with permissions."""
    permissions: list[PermissionResponse] = []

    model_config = {"from_attributes": True}
