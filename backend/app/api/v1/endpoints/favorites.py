"""User favorites endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.link import Link
from app.models.associations import user_favorites, NavigationGroupPermission, LinkPermission
from app.schemas.link import LinkResponse
from app.api.deps import get_current_active_user


router = APIRouter()


async def _permitted_group_ids(
    db: AsyncSession, user: User
) -> list[UUID] | None:
    """Return permitted navigation group IDs for a non-superuser.

    Returns None if the user has 'all' access (navigation_group_id IS NULL).
    Returns a list of specific group UUIDs otherwise.
    """
    user_group_ids = [ug.id for ug in user.user_groups]
    user_filter = [NavigationGroupPermission.user_id == user.id]
    if user_group_ids:
        user_filter.append(
            NavigationGroupPermission.user_group_id.in_(user_group_ids)
        )

    # Check for "all" permission
    all_stmt = select(NavigationGroupPermission).where(
        NavigationGroupPermission.navigation_group_id.is_(None),
        or_(*user_filter),
    )
    result = await db.execute(all_stmt)
    if result.scalar_one_or_none() is not None:
        return None  # has access to everything

    # Get specific permitted group IDs
    ids_stmt = select(
        NavigationGroupPermission.navigation_group_id
    ).where(
        NavigationGroupPermission.navigation_group_id.isnot(None),
        or_(*user_filter),
    )
    result = await db.execute(ids_stmt)
    return [row[0] for row in result.fetchall()]


@router.get("/", response_model=List[LinkResponse])
async def list_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[LinkResponse]:
    """List current user's favorited links (filtered by permissions)."""
    base_stmt = (
        select(Link)
        .join(user_favorites, user_favorites.c.link_id == Link.id)
        .where(
            user_favorites.c.user_id == current_user.id,
            Link.is_active == True,
        )
    )

    if not current_user.is_superuser:
        permitted = await _permitted_group_ids(db, current_user)
        if permitted is not None:
            user_group_ids = [ug.id for ug in current_user.user_groups]
            link_filter = [LinkPermission.user_id == current_user.id]
            if user_group_ids:
                link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))
            direct_link_ids_stmt = select(
                LinkPermission.link_id
            ).where(or_(*link_filter))

            base_stmt = base_stmt.where(
                or_(
                    Link.navigation_group_id.in_(permitted),
                    Link.id.in_(direct_link_ids_stmt),
                )
            )

    stmt = base_stmt.order_by(user_favorites.c.created_at.desc())
    result = await db.execute(stmt)
    links = result.scalars().all()
    return [LinkResponse.model_validate(link) for link in links]


@router.get("/ids", response_model=List[str])
async def list_favorite_ids(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[str]:
    """Return just the link IDs the user has favorited (filtered by permissions)."""
    base_stmt = (
        select(user_favorites.c.link_id)
        .join(Link, user_favorites.c.link_id == Link.id)
        .where(
            user_favorites.c.user_id == current_user.id,
            Link.is_active == True,
        )
    )

    if not current_user.is_superuser:
        permitted = await _permitted_group_ids(db, current_user)
        if permitted is not None:
            user_group_ids = [ug.id for ug in current_user.user_groups]
            link_filter = [LinkPermission.user_id == current_user.id]
            if user_group_ids:
                link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))
            direct_link_ids_stmt = select(
                LinkPermission.link_id
            ).where(or_(*link_filter))

            base_stmt = base_stmt.where(
                or_(
                    Link.navigation_group_id.in_(permitted),
                    Link.id.in_(direct_link_ids_stmt),
                )
            )

    result = await db.execute(base_stmt)
    return [str(row[0]) for row in result.fetchall()]


@router.post("/{link_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Add a link to the current user's favorites."""
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
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
    await db.commit()

    return {"message": "Link added to favorites"}


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    link_id: UUID,
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
    await db.commit()
