"""Permission management endpoints."""

from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import PermissionResponse
from app.api.deps import require_superuser
from app.config import settings


router = APIRouter()


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> List[PermissionResponse]:
    """
    List all permissions (paginated, admin only).

    Args:
        db: Database session
        current_user: Current superuser
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of permissions
    """
    stmt = (
        select(Permission)
        .offset(skip)
        .limit(limit)
        .order_by(Permission.resource, Permission.action)
    )
    result = await db.execute(stmt)
    permissions = result.scalars().all()

    return [PermissionResponse.model_validate(permission) for permission in permissions]
