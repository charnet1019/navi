"""Navigation group-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class NavigationGroupBase(BaseModel):
    """Base navigation group schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=255)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class NavigationGroupCreate(NavigationGroupBase):
    """Schema for creating a new navigation group."""
    pass


class NavigationGroupUpdate(BaseModel):
    """Schema for updating an existing navigation group."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class NavigationGroupResponse(BaseModel):
    """Schema for navigation group response."""
    id: UUID
    name: str
    description: Optional[str]
    icon: Optional[str]
    sort_order: int
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NavigationGroupWithLinks(NavigationGroupResponse):
    """Schema for navigation group with links included."""
    links: list["LinkResponse"] = []

    model_config = {"from_attributes": True}


# Import at the end to avoid circular imports
from app.schemas.link import LinkResponse
NavigationGroupWithLinks.model_rebuild()
