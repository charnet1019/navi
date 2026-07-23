"""User group management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user_group import UserGroup
from app.models.user import User
from app.models.associations import NavigationGroupPermission, LinkPermission
from app.models.navigation_group import NavigationGroup
from app.models.link import Link
from app.schemas.user_group import (
    UserGroupCreate,
    UserGroupUpdate,
    UserGroupResponse,
    UserGroupWithMembers,
)
from app.api.deps import require_superuser
from app.config import settings
from app.core.permissions import invalidate_user_permissions_cache
from app.core.navigation_access import build_group_path
from app.services.audit import build_field_changes, record_audit_log


router = APIRouter()


@router.get("/", response_model=List[UserGroupResponse])
async def list_user_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> List[UserGroupResponse]:
    """
    List user groups (paginated, admin only).

    Args:
        db: Database session
        current_user: Current superuser
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of user groups
    """
    stmt = (
        select(UserGroup)
        .offset(skip)
        .limit(limit)
        .order_by(UserGroup.created_at.desc())
    )
    result = await db.execute(stmt)
    groups = result.scalars().all()

    return [UserGroupResponse.model_validate(group) for group in groups]


@router.post("/", response_model=UserGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_user_group(
    group_data: UserGroupCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserGroupResponse:
    """
    Create user group (admin only).

    Args:
        group_data: User group creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created user group

    Raises:
        HTTPException: If group name already exists
    """
    # Check if group name already exists
    stmt = select(UserGroup).where(UserGroup.name == group_data.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User group name already exists",
        )

    # Create new user group
    new_group = UserGroup(
        name=group_data.name,
        description=group_data.description,
    )

    db.add(new_group)
    await db.flush()
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user_group.create",
        resource_type="user_group",
        resource_id=new_group.id,
        changes={"name": new_group.name, "description": new_group.description},
        request=request,
    )
    await db.commit()
    await db.refresh(new_group)

    return UserGroupResponse.model_validate(new_group)


@router.get("/{group_id}", response_model=UserGroupWithMembers)
async def get_user_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserGroupWithMembers:
    """
    Get group details with members (admin only).

    Args:
        group_id: User group ID
        db: Database session
        current_user: Current superuser

    Returns:
        User group details with members

    Raises:
        HTTPException: If group not found
    """
    stmt = (
        select(UserGroup)
        .where(UserGroup.id == group_id)
        .options(selectinload(UserGroup.members))
    )
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    return UserGroupWithMembers.model_validate(group)


@router.put("/{group_id}", response_model=UserGroupResponse)
async def update_user_group(
    group_id: UUID,
    group_data: UserGroupUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserGroupResponse:
    """
    Update group (admin only).

    Args:
        group_id: User group ID
        group_data: User group update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated user group

    Raises:
        HTTPException: If group not found or name already exists
    """
    stmt = select(UserGroup).where(UserGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    # Check if name is being changed and already exists
    if group_data.name and group_data.name != group.name:
        stmt = select(UserGroup).where(UserGroup.name == group_data.name)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User group name already exists",
            )

    original_group_name = group.name
    # Update group fields
    update_data = group_data.model_dump(exclude_unset=True)
    field_changes = build_field_changes(
        {"name": group.name, "description": group.description},
        update_data,
    )
    if not field_changes:
        return UserGroupResponse.model_validate(group)

    for field, value in update_data.items():
        setattr(group, field, value)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user_group.update",
        resource_type="user_group",
        resource_id=group_id,
        changes={"group_name": original_group_name, "field_changes": field_changes},
        request=request,
    )
    await db.commit()
    await db.refresh(group)

    return UserGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_group(
    group_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Delete group (admin only).

    Args:
        group_id: User group ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If group not found
    """
    stmt = (
        select(UserGroup)
        .where(UserGroup.id == group_id)
        .options(selectinload(UserGroup.members))
    )
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    # Invalidate cache for all members before deletion
    for member in group.members:
        await invalidate_user_permissions_cache(member.id)

    deleted_group = {
        "name": group.name,
        "description": group.description,
        "member_ids": [str(member.id) for member in group.members],
    }
    await db.delete(group)
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user_group.delete",
        resource_type="user_group",
        resource_id=group_id,
        changes=deleted_group,
        request=request,
    )
    await db.commit()


@router.post("/{group_id}/members", response_model=UserGroupWithMembers)
async def add_user_to_group(
    group_id: UUID,
    user_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserGroupWithMembers:
    """
    Add user to group (admin only).

    Args:
        group_id: User group ID
        user_id: User ID to add
        db: Database session
        current_user: Current superuser

    Returns:
        Updated user group with members

    Raises:
        HTTPException: If group or user not found, or user already in group
    """
    # Fetch group with members
    stmt = (
        select(UserGroup)
        .where(UserGroup.id == group_id)
        .options(selectinload(UserGroup.members))
    )
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    # Fetch user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is already in group
    if user in group.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group",
        )

    # Add user to group
    group.members.append(user)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user_group.member_add",
        resource_type="user_group",
        resource_id=group_id,
        changes={
            "group_name": group.name,
            "member_user_id": str(user_id),
            "member_username": user.username,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(group)

    # Invalidate user's permissions cache
    await invalidate_user_permissions_cache(user_id)

    return UserGroupWithMembers.model_validate(group)


@router.delete("/{group_id}/members/{user_id}", response_model=UserGroupWithMembers)
async def remove_user_from_group(
    group_id: UUID,
    user_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserGroupWithMembers:
    """
    Remove user from group (admin only).

    Args:
        group_id: User group ID
        user_id: User ID to remove
        db: Database session
        current_user: Current superuser

    Returns:
        Updated user group with members

    Raises:
        HTTPException: If group or user not found, or user not in group
    """
    # Fetch group with members
    stmt = (
        select(UserGroup)
        .where(UserGroup.id == group_id)
        .options(selectinload(UserGroup.members))
    )
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    # Find user in group members
    user_to_remove = None
    for member in group.members:
        if member.id == user_id:
            user_to_remove = member
            break

    if user_to_remove is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group",
        )

    # Remove user from group
    group.members.remove(user_to_remove)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user_group.member_remove",
        resource_type="user_group",
        resource_id=group_id,
        changes={
            "group_name": group.name,
            "member_user_id": str(user_id),
            "member_username": user_to_remove.username,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(group)

    # Invalidate user's permissions cache
    await invalidate_user_permissions_cache(user_id)

    return UserGroupWithMembers.model_validate(group)


@router.get("/{group_id}/authorized-assets")
async def get_user_group_authorized_assets(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Get authorized assets (nav groups + links) for a user group (admin only)."""
    stmt = select(UserGroup).where(UserGroup.id == group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found",
        )

    # Fetch all navigation groups to build hierarchy paths with limit
    all_groups_stmt = select(NavigationGroup).limit(settings.MAX_NAVIGATION_GROUPS)
    all_groups_result = await db.execute(all_groups_stmt)
    all_groups = {g.id: g for g in all_groups_result.scalars().all()}

    # Nav group permissions assigned to this user group
    nav_stmt = (
        select(
            NavigationGroupPermission,
            NavigationGroup.name.label("group_name"),
        )
        .outerjoin(
            NavigationGroup,
            NavigationGroupPermission.navigation_group_id == NavigationGroup.id,
        )
        .where(NavigationGroupPermission.user_group_id == group_id)
        .order_by(NavigationGroupPermission.granted_at.desc())
    )
    nav_result = await db.execute(nav_stmt)
    nav_rows = nav_result.all()

    nav_group_permissions = [
        {
            "permission_id": str(row.NavigationGroupPermission.id),
            "navigation_group_id": (
                str(row.NavigationGroupPermission.navigation_group_id)
                if row.NavigationGroupPermission.navigation_group_id
                else None
            ),
            "navigation_group_name": build_group_path(row.NavigationGroupPermission.navigation_group_id, all_groups),
            "granted_at": row.NavigationGroupPermission.granted_at.isoformat(),
        }
        for row in nav_rows
    ]

    # Link permissions assigned to this user group
    link_stmt = (
        select(
            LinkPermission,
            Link.name.label("link_name"),
            Link.navigation_group_id.label("group_id"),
        )
        .join(Link, LinkPermission.link_id == Link.id)
        .where(LinkPermission.user_group_id == group_id)
        .order_by(LinkPermission.granted_at.desc())
    )
    link_result = await db.execute(link_stmt)
    link_rows = link_result.all()

    link_permissions = [
        {
            "permission_id": str(row.LinkPermission.id),
            "link_id": str(row.LinkPermission.link_id),
            "link_name": row.link_name,
            "navigation_group_name": build_group_path(row.group_id, all_groups),
            "granted_at": row.LinkPermission.granted_at.isoformat(),
        }
        for row in link_rows
    ]

    return {
        "nav_group_permissions": nav_group_permissions,
        "link_permissions": link_permissions,
    }
