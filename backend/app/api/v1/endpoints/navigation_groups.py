"""Navigation group management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.navigation_group import NavigationGroup
from app.models.link import Link
from app.models.associations import NavigationGroupPermission, LinkPermission
from app.models.user_group import UserGroup
from app.schemas.navigation_group import (
    NavigationGroupCreate,
    NavigationGroupUpdate,
    NavigationGroupResponse,
)
from app.schemas.permission import (
    GrantPermissionRequest,
    NavGroupPermissionResponse,
)
from app.api.deps import require_superuser, get_current_active_user
from app.config import settings


router = APIRouter()


@router.get("/", response_model=List[NavigationGroupResponse])
async def list_navigation_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> List[NavigationGroupResponse]:
    """
    List navigation groups (filtered by user permissions).

    Args:
        db: Database session
        current_user: Current active user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of navigation groups the user has access to
    """
    if current_user.is_superuser:
        stmt = select(NavigationGroup).where(
            NavigationGroup.is_active == True
        ).offset(skip).limit(limit).order_by(
            NavigationGroup.sort_order, NavigationGroup.name
        )
    else:
        user_group_ids = [ug.id for ug in current_user.user_groups]
        user_filter = [NavigationGroupPermission.user_id == current_user.id]
        if user_group_ids:
            user_filter.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))

        # Check for "all" permission (navigation_group_id IS NULL)
        all_perm_stmt = select(NavigationGroupPermission).where(
            NavigationGroupPermission.navigation_group_id.is_(None),
            or_(*user_filter),
        )
        all_perm = await db.execute(all_perm_stmt)
        has_all_access = all_perm.scalar_one_or_none() is not None

        if has_all_access:
            stmt = select(NavigationGroup).where(
                NavigationGroup.is_active == True
            ).offset(skip).limit(limit).order_by(
                NavigationGroup.sort_order, NavigationGroup.name
            )
        else:
            permitted_ids_stmt = select(
                NavigationGroupPermission.navigation_group_id
            ).where(
                NavigationGroupPermission.navigation_group_id.isnot(None),
                or_(*user_filter),
            )

            # Groups containing links directly permitted to the user
            link_filter = [LinkPermission.user_id == current_user.id]
            if user_group_ids:
                link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))
            direct_group_ids_stmt = (
                select(Link.navigation_group_id)
                .join(LinkPermission, LinkPermission.link_id == Link.id)
                .where(or_(*link_filter))
                .distinct()
            )

            stmt = select(NavigationGroup).where(
                NavigationGroup.is_active == True,
                or_(
                    NavigationGroup.id.in_(permitted_ids_stmt),
                    NavigationGroup.id.in_(direct_group_ids_stmt),
                ),
            ).offset(skip).limit(limit).order_by(
                NavigationGroup.sort_order, NavigationGroup.name
            )

    result = await db.execute(stmt)
    groups = result.scalars().all()
    return [NavigationGroupResponse.model_validate(group) for group in groups]


@router.post("/", response_model=NavigationGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_navigation_group(
    group_data: NavigationGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> NavigationGroupResponse:
    """
    Create navigation group (admin only).

    Args:
        group_data: Navigation group creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created navigation group
    """
    # Create new navigation group
    new_group = NavigationGroup(
        name=group_data.name,
        description=group_data.description,
        icon=group_data.icon,
        sort_order=group_data.sort_order,
        is_active=group_data.is_active,
        created_by=current_user.id,
    )

    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)

    return NavigationGroupResponse.model_validate(new_group)


class ReorderItem(BaseModel):
    id: UUID
    sort_order: int


@router.put("/reorder", response_model=List[NavigationGroupResponse])
async def reorder_navigation_groups(
    items: List[ReorderItem],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[NavigationGroupResponse]:
    """Batch update sort order for navigation groups (admin only)."""
    stmt = select(NavigationGroup).where(
        NavigationGroup.id.in_([item.id for item in items])
    )
    result = await db.execute(stmt)
    groups_map = {g.id: g for g in result.scalars().all()}

    for item in items:
        group = groups_map.get(item.id)
        if group:
            group.sort_order = item.sort_order

    await db.commit()

    updated = []
    for item in items:
        group = groups_map.get(item.id)
        if group:
            await db.refresh(group)
            updated.append(NavigationGroupResponse.model_validate(group))
    return updated


@router.get("/all-permissions", response_model=List[NavGroupPermissionResponse])
async def list_all_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[NavGroupPermissionResponse]:
    """List 'all' permissions (navigation_group_id IS NULL) (admin only)."""
    stmt = (
        select(
            NavigationGroupPermission,
            User.username.label("user_name"),
            UserGroup.name.label("user_group_name"),
        )
        .outerjoin(User, NavigationGroupPermission.user_id == User.id)
        .outerjoin(UserGroup, NavigationGroupPermission.user_group_id == UserGroup.id)
        .where(NavigationGroupPermission.navigation_group_id.is_(None))
        .order_by(NavigationGroupPermission.granted_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        NavGroupPermissionResponse(
            id=row.NavigationGroupPermission.id,
            navigation_group_id=None,
            user_id=row.NavigationGroupPermission.user_id,
            user_group_id=row.NavigationGroupPermission.user_group_id,
            user_name=row.user_name,
            user_group_name=row.user_group_name,
            granted_at=row.NavigationGroupPermission.granted_at,
            granted_by=row.NavigationGroupPermission.granted_by,
        )
        for row in rows
    ]


@router.post("/all-permissions", status_code=status.HTTP_201_CREATED)
async def grant_all_permission(
    body: GrantPermissionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Grant 'all' navigation group access for user or user_group (admin only)."""
    user_id = body.user_id
    user_group_id = body.user_group_id

    if (user_id is None and user_group_id is None) or (user_id is not None and user_group_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly one of user_id or user_group_id",
        )

    if user_id:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    else:
        stmt = select(UserGroup).where(UserGroup.id == user_group_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User group not found")

    # Check duplicate
    dup_stmt = select(NavigationGroupPermission).where(
        NavigationGroupPermission.navigation_group_id.is_(None),
        NavigationGroupPermission.user_id == user_id if user_id else NavigationGroupPermission.user_group_id == user_group_id,
    )
    result = await db.execute(dup_stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")

    permission = NavigationGroupPermission(
        navigation_group_id=None,
        user_id=user_id,
        user_group_id=user_group_id,
        granted_by=current_user.id,
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)

    return {"message": "Permission granted successfully", "permission_id": str(permission.id)}


@router.delete("/all-permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_permission(
    permission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """Revoke 'all' navigation group access (admin only)."""
    stmt = select(NavigationGroupPermission).where(
        NavigationGroupPermission.id == permission_id,
        NavigationGroupPermission.navigation_group_id.is_(None),
    )
    result = await db.execute(stmt)
    permission = result.scalar_one_or_none()

    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    await db.delete(permission)
    await db.commit()


@router.get("/{group_id}", response_model=NavigationGroupResponse)
async def get_navigation_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> NavigationGroupResponse:
    """
    Get navigation group details (if user has access).

    Args:
        group_id: Navigation group ID
        db: Database session
        current_user: Current active user

    Returns:
        Navigation group details

    Raises:
        HTTPException: If group not found or user doesn't have access
    """
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    # Permission check for non-superusers
    if not current_user.is_superuser:
        user_group_ids = [ug.id for ug in current_user.user_groups]
        user_filter = [NavigationGroupPermission.user_id == current_user.id]
        if user_group_ids:
            user_filter.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))

        # Check "all" or specific group permission
        perm_stmt = select(NavigationGroupPermission).where(
            or_(
                NavigationGroupPermission.navigation_group_id.is_(None),
                NavigationGroupPermission.navigation_group_id == group_id,
            ),
            or_(*user_filter),
        )
        perm_result = await db.execute(perm_stmt)
        has_access = perm_result.scalar_one_or_none() is not None

        if not has_access:
            # Check if user has direct link permission in this group
            link_filter = [LinkPermission.user_id == current_user.id]
            if user_group_ids:
                link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))
            link_stmt = (
                select(LinkPermission.id)
                .join(Link, LinkPermission.link_id == Link.id)
                .where(
                    Link.navigation_group_id == group_id,
                    or_(*link_filter),
                )
                .limit(1)
            )
            link_result = await db.execute(link_stmt)
            if link_result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Navigation group not found",
                )

    return NavigationGroupResponse.model_validate(group)


@router.put("/{group_id}", response_model=NavigationGroupResponse)
async def update_navigation_group(
    group_id: UUID,
    group_data: NavigationGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> NavigationGroupResponse:
    """
    Update navigation group (admin only).

    Args:
        group_id: Navigation group ID
        group_data: Navigation group update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated navigation group

    Raises:
        HTTPException: If group not found
    """
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    # Update group fields (immutable pattern)
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)

    return NavigationGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_navigation_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Delete navigation group (admin only).

    Args:
        group_id: Navigation group ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If group not found
    """
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    await db.delete(group)
    await db.commit()


@router.put("/{group_id}/sort-order", response_model=NavigationGroupResponse)
async def update_navigation_group_sort_order(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    sort_order: int = Query(..., ge=0),
) -> NavigationGroupResponse:
    """
    Update navigation group sort order (admin only).

    Args:
        group_id: Navigation group ID
        sort_order: New sort order
        db: Database session
        current_user: Current superuser

    Returns:
        Updated navigation group

    Raises:
        HTTPException: If group not found
    """
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    group.sort_order = sort_order
    await db.commit()
    await db.refresh(group)

    return NavigationGroupResponse.model_validate(group)


@router.get("/{group_id}/permissions", response_model=List[NavGroupPermissionResponse])
async def list_navigation_group_permissions(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[NavGroupPermissionResponse]:
    """List permissions for a navigation group (admin only)."""
    # Verify navigation group exists
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    # Fetch permissions with user/user_group names via left joins
    stmt = (
        select(
            NavigationGroupPermission,
            User.username.label("user_name"),
            UserGroup.name.label("user_group_name"),
        )
        .outerjoin(User, NavigationGroupPermission.user_id == User.id)
        .outerjoin(UserGroup, NavigationGroupPermission.user_group_id == UserGroup.id)
        .where(NavigationGroupPermission.navigation_group_id == group_id)
        .order_by(NavigationGroupPermission.granted_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        NavGroupPermissionResponse(
            id=row.NavigationGroupPermission.id,
            navigation_group_id=row.NavigationGroupPermission.navigation_group_id,
            user_id=row.NavigationGroupPermission.user_id,
            user_group_id=row.NavigationGroupPermission.user_group_id,
            user_name=row.user_name,
            user_group_name=row.user_group_name,
            granted_at=row.NavigationGroupPermission.granted_at,
            granted_by=row.NavigationGroupPermission.granted_by,
        )
        for row in rows
    ]


@router.post("/{group_id}/permissions", status_code=status.HTTP_201_CREATED)
async def grant_navigation_group_permission(
    group_id: UUID,
    body: GrantPermissionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """
    Grant access to navigation group for user or user_group (admin only).

    Args:
        group_id: Navigation group ID
        body: Request body with user_id or user_group_id
        db: Database session
        current_user: Current superuser

    Returns:
        Success message with permission ID

    Raises:
        HTTPException: If validation fails
    """
    user_id = body.user_id
    user_group_id = body.user_group_id

    # Validate that exactly one of user_id or user_group_id is provided
    if (user_id is None and user_group_id is None) or (user_id is not None and user_group_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly one of user_id or user_group_id",
        )

    # Verify navigation group exists
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    # Verify user or user_group exists
    if user_id:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    else:
        stmt = select(UserGroup).where(UserGroup.id == user_group_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User group not found",
            )

    # Check if permission already exists
    stmt = select(NavigationGroupPermission).where(
        NavigationGroupPermission.navigation_group_id == group_id,
        NavigationGroupPermission.user_id == user_id if user_id else NavigationGroupPermission.user_group_id == user_group_id,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists",
        )

    # Create permission
    permission = NavigationGroupPermission(
        navigation_group_id=group_id,
        user_id=user_id,
        user_group_id=user_group_id,
        granted_by=current_user.id,
    )

    db.add(permission)
    await db.commit()
    await db.refresh(permission)

    return {
        "message": "Permission granted successfully",
        "permission_id": str(permission.id),
    }


@router.delete("/{group_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_navigation_group_permission(
    group_id: UUID,
    permission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Revoke access to navigation group (admin only).

    Args:
        group_id: Navigation group ID
        permission_id: Permission ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If permission not found
    """
    stmt = select(NavigationGroupPermission).where(
        NavigationGroupPermission.id == permission_id,
        NavigationGroupPermission.navigation_group_id == group_id,
    )
    result = await db.execute(stmt)
    permission = result.scalar_one_or_none()

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    await db.delete(permission)
    await db.commit()

