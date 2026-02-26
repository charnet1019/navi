"""Link-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl


class LinkBase(BaseModel):
    """Base link schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    url: str = Field(..., min_length=1, max_length=500)
    icon_path: Optional[str] = Field(None, max_length=255)
    navigation_group_id: UUID
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True
    open_in_new_tab: bool = True


class LinkCreate(LinkBase):
    """Schema for creating a new link."""
    pass


class LinkUpdate(BaseModel):
    """Schema for updating an existing link."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    icon_path: Optional[str] = Field(None, max_length=255)
    navigation_group_id: Optional[UUID] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    open_in_new_tab: Optional[bool] = None


class LinkResponse(BaseModel):
    """Schema for link response."""
    id: UUID
    name: str
    description: Optional[str]
    url: str
    icon_path: Optional[str]
    navigation_group_id: UUID
    sort_order: int
    is_active: bool
    open_in_new_tab: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
