"""Shared request schemas for batch sort-order updates."""

from uuid import UUID
from pydantic import BaseModel


class ReorderItem(BaseModel):
    """Sort-order update for an entity referenced by its own id."""
    id: UUID
    sort_order: int


class FavoriteReorderItem(BaseModel):
    """Sort-order update for a favorite, referenced by the underlying link id."""
    link_id: UUID
    sort_order: int
