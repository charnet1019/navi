"""User favorites endpoints."""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.navigation_access import NavigationAccessScope, accessible_link_condition, build_navigation_access_scope
from app.database import get_db
from app.models.associations import user_favorites
from app.models.link import Link
from app.models.user import User
from app.schemas.link import LinkResponse
from app.schemas.reorder import FavoriteReorderItem
from app.services.audit import record_audit_log


router = APIRouter()


def _can_access_link(scope: NavigationAccessScope, link: Link) -> bool:
    return (
        scope.has_all_access
        or link.navigation_group_id in scope.visible_group_ids
        or link.id in scope.direct_link_ids
    )


@router.get("/", response_model=List[LinkResponse])
async def list_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[LinkResponse]:
    """List current user's favorited links (filtered by permissions)."""
    stmt = (
        select(Link)
        .join(user_favorites, user_favorites.c.link_id == Link.id)
        .where(
            user_favorites.c.user_id == current_user.id,
            Link.is_active == True,
        )
    )

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access:
            stmt = stmt.where(accessible_link_condition(scope))

    stmt = stmt.order_by(user_favorites.c.sort_order, user_favorites.c.created_at.desc())
    result = await db.execute(stmt)
    return [LinkResponse.model_validate(link) for link in result.scalars().all()]


@router.get("/ids", response_model=List[str])
async def list_favorite_ids(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[str]:
    """Return just the link IDs the user has favorited (filtered by permissions)."""
    stmt = (
        select(user_favorites.c.link_id)
        .join(Link, user_favorites.c.link_id == Link.id)
        .where(
            user_favorites.c.user_id == current_user.id,
            Link.is_active == True,
        )
    )

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access:
            stmt = stmt.where(accessible_link_condition(scope))

    result = await db.execute(stmt)
    return [str(row[0]) for row in result.fetchall()]


@router.post("/{link_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    link_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Add a link to the current user's favorites."""
    stmt = select(Link).where(Link.id == link_id, Link.is_active == True)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not _can_access_link(scope, link):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found",
            )

    existing = await db.execute(
        select(user_favorites).where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.link_id == link_id,
        )
    )
    if existing.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Link already favorited",
        )

    await db.execute(
        user_favorites.insert().values(
            user_id=current_user.id,
            link_id=link_id,
        )
    )
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="favorite.add",
        resource_type="favorite",
        resource_id=link_id,
        changes={"link_name": link.name},
        request=request,
    )
    await db.commit()

    return {"message": "Link added to favorites"}


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    link_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Remove a link from the current user's favorites."""
    result = await db.execute(
        select(user_favorites).where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.link_id == link_id,
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    await db.execute(
        delete(user_favorites).where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.link_id == link_id,
        )
    )
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="favorite.remove",
        resource_type="favorite",
        resource_id=link_id,
        request=request,
    )
    await db.commit()


@router.put("/reorder", response_model=List[LinkResponse])
async def reorder_favorites(
    items: List[FavoriteReorderItem],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[LinkResponse]:
    """Batch update sort order for user's favorite links."""
    if not items:
        return await list_favorites(db, current_user)

    requested_ids = [item.link_id for item in items]
    if len(set(requested_ids)) != len(requested_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate link_id in reorder request",
        )
    existing_result = await db.execute(
        select(user_favorites.c.link_id).where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.link_id.in_(requested_ids),
        )
    )
    existing_ids = set(existing_result.scalars().all())
    missing_ids = [str(link_id) for link_id in requested_ids if link_id not in existing_ids]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Favorite not found: {', '.join(missing_ids)}",
        )

    for item in items:
        await db.execute(
            update(user_favorites)
            .where(
                user_favorites.c.user_id == current_user.id,
                user_favorites.c.link_id == item.link_id,
            )
            .values(sort_order=item.sort_order)
        )

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="favorite.reorder",
        resource_type="favorite",
        changes={
            "items": [
                {"link_id": str(item.link_id), "sort_order": item.sort_order}
                for item in items
            ],
        },
        request=request,
    )
    await db.commit()
    return await list_favorites(db, current_user)
