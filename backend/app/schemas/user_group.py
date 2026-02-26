"""User group-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserGroupBase(BaseModel):
    """Base user group schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class UserGroupCreate(UserGroupBase):
    """Schema for creating a new user group."""
    pass


class UserGroupUpdate(BaseModel):
    """Schema for updating an existing user group."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class UserGroupResponse(BaseModel):
    """Schema for user group response."""
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserGroupMember(BaseModel):
    """Schema for user group member (simplified user info)."""
    id: UUID
    username: str
    email: str
    full_name: str | None

    model_config = {"from_attributes": True}


class UserGroupWithMembers(UserGroupResponse):
    """Schema for user group response with members."""
    members: list[UserGroupMember] = []

    model_config = {"from_attributes": True}
