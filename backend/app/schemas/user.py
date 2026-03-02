"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserGroupBrief(BaseModel):
    """Brief user group info for embedding in user responses."""
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    user_group_ids: list[UUID] = []


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    user_group_ids: list[UUID] | None = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    user_groups: list[UserGroupBrief] = []
    is_locked: Optional[bool] = None
    locked_until: Optional[datetime] = None

    model_config = {"from_attributes": True}
