"""Link-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def validate_link_url(value: str) -> str:
    """Allow only HTTP(S) URLs for rendered link anchors."""
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be a valid http:// or https:// address")
    return url


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

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_link_url(value)


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

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_link_url(value) if value is not None else value


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
