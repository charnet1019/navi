"""User management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.models.user_group import UserGroup
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password
from app.utils.password import validate_password
from app.api.deps import require_superuser, get_current_active_user
from app.core.permissions import get_user_permissions, invalidate_user_permissions_cache
from app.models.associations import NavigationGroupPermission, LinkPermission, user_group_members
from app.models.navigation_group import NavigationGroup
from app.models.link import Link
from app.models.system_setting import SystemSetting
from app.config import settings
from app.redis import get_redis

LOGIN_ATTEMPT_PREFIX = "login_attempts:"


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1, max_length=100)


router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> List[UserResponse]:
    """
    List users (paginated, admin only).

    Args:
        db: Database session
        current_user: Current superuser
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of users with lock status
    """
    stmt = (
        select(User)
        .options(selectinload(User.user_groups))
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Get login settings for max_attempts check
    keys = ["max_login_attempts"]
    settings_stmt = select(SystemSetting).where(SystemSetting.key.in_(keys))
    settings_result = await db.execute(settings_stmt)
    rows = {s.key: s.value for s in settings_result.scalars().all()}
    max_attempts = int(rows.get("max_login_attempts", 3))

    # Check lock status for each user
    redis = await get_redis()
    user_responses = []
    for user in users:
        user_dict = UserResponse.model_validate(user).model_dump()

        # Check if user is locked
        attempt_key = f"{LOGIN_ATTEMPT_PREFIX}{user.username}"
        attempts = await redis.get(attempt_key)

        if attempts is not None and int(attempts) >= max_attempts:
            user_dict["is_locked"] = True
            ttl = await redis.ttl(attempt_key)
            if ttl > 0:
                from datetime import datetime, timedelta, timezone
                user_dict["locked_until"] = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        else:
            user_dict["is_locked"] = False

        user_responses.append(UserResponse(**user_dict))

    return user_responses


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserResponse:
    """
    Create user (admin only).

    Args:
        user_data: User creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username already exists
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password rules
    pwd_errors = await validate_password(user_data.password, db)
    if pwd_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="；".join(pwd_errors),
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
    )

    db.add(new_user)
    await db.flush()

    # Assign user to groups
    group_ids = list(user_data.user_group_ids) if user_data.user_group_ids else []
    if not group_ids and not new_user.is_superuser:
        default_group = await db.execute(
            select(UserGroup).where(UserGroup.name == 'default')
        )
        default_group = default_group.scalar_one_or_none()
        if default_group:
            group_ids = [default_group.id]
    if group_ids:
        await db.execute(
            user_group_members.insert(),
            [{"user_group_id": gid, "user_id": new_user.id} for gid in group_ids]
        )

    await db.commit()

    # Re-fetch with groups loaded
    stmt = (
        select(User)
        .where(User.id == new_user.id)
        .options(selectinload(User.user_groups))
    )
    result = await db.execute(stmt)
    new_user = result.scalar_one()

    return UserResponse.model_validate(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserResponse:
    """
    Get user details (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current superuser

    Returns:
        User details

    Raises:
        HTTPException: If user not found
    """
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_groups))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserResponse:
    """
    Update user (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or email already exists
    """
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_groups))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if email is being changed and already exists
    if user_data.email and user_data.email != user.email:
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update user groups if provided
    if user_data.user_group_ids is not None:
        await db.execute(
            user_group_members.delete().where(user_group_members.c.user_id == user_id)
        )
        if user_data.user_group_ids:
            await db.execute(
                user_group_members.insert(),
                [{"user_group_id": gid, "user_id": user_id} for gid in user_data.user_group_ids]
            )

    # Update user fields (immutable pattern)
    update_data = user_data.model_dump(exclude_unset=True, exclude={"user_group_ids"})
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()

    # Re-fetch with groups loaded
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_groups))
    )
    result = await db.execute(stmt)
    user = result.scalar_one()

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Delete user (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If user not found or trying to delete self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()

    # Invalidate permissions cache
    await invalidate_user_permissions_cache(user_id)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: UUID,
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Reset user password (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate password rules
    pwd_errors = await validate_password(body.new_password, db)
    if pwd_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="；".join(pwd_errors),
        )

    user.hashed_password = hash_password(body.new_password)
    await db.commit()

    return {"message": "Password reset successfully"}


@router.post("/{user_id}/disable", response_model=UserResponse)
async def disable_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserResponse:
    """Disable user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable yourself",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = False
    await db.commit()

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.user_groups))
    )
    return UserResponse.model_validate(result.scalar_one())


@router.post("/{user_id}/enable", response_model=UserResponse)
async def enable_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> UserResponse:
    """Enable user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    await db.commit()

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.user_groups))
    )
    return UserResponse.model_validate(result.scalar_one())


@router.get("/{user_id}/permissions")
async def get_user_permissions_endpoint(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """
    Get effective permissions for a user.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current superuser

    Returns:
        User permissions

    Raises:
        HTTPException: If user not found
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    permissions = await get_user_permissions(user_id, db)

    return {
        "user_id": str(user_id),
        "permissions": sorted(list(permissions)),
    }


@router.get("/{user_id}/authorized-assets")
async def get_user_authorized_assets(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Get authorized assets (nav groups + links) for a user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Fetch all navigation groups to build hierarchy paths with limit
    all_groups_stmt = select(NavigationGroup).limit(settings.MAX_NAVIGATION_GROUPS)
    all_groups_result = await db.execute(all_groups_stmt)
    all_groups = {g.id: g for g in all_groups_result.scalars().all()}

    def build_group_path(group_id, groups_map, max_depth=None):
        """Build full hierarchy path for a navigation group with depth limit and cycle detection."""
        if group_id is None:
            return "全部"
        if max_depth is None:
            max_depth = settings.MAX_HIERARCHY_DEPTH

        path_parts = []
        current = groups_map.get(group_id)
        visited = set()
        depth = 0

        while current and depth < max_depth:
            if current.id in visited:
                # Cycle detected, break to prevent infinite loop
                break
            visited.add(current.id)
            path_parts.insert(0, current.name)
            current = groups_map.get(current.parent_id) if current.parent_id else None
            depth += 1

        return "/".join(path_parts) if path_parts else ""

    # Nav group permissions directly assigned to this user
    nav_stmt = (
        select(
            NavigationGroupPermission,
            NavigationGroup.name.label("group_name"),
        )
        .outerjoin(
            NavigationGroup,
            NavigationGroupPermission.navigation_group_id == NavigationGroup.id,
        )
        .where(NavigationGroupPermission.user_id == user_id)
        .order_by(NavigationGroupPermission.granted_at.desc())
    )
    nav_result = await db.execute(nav_stmt)
    nav_rows = nav_result.all()

    nav_group_permissions = [
        {
            "permission_id": str(row.NavigationGroupPermission.id),
            "navigation_group_id": str(row.NavigationGroupPermission.navigation_group_id) if row.NavigationGroupPermission.navigation_group_id else None,
            "navigation_group_name": build_group_path(row.NavigationGroupPermission.navigation_group_id, all_groups),
            "granted_at": row.NavigationGroupPermission.granted_at.isoformat(),
        }
        for row in nav_rows
    ]

    # Link permissions directly assigned to this user
    link_stmt = (
        select(
            LinkPermission,
            Link.name.label("link_name"),
            Link.navigation_group_id.label("group_id"),
        )
        .join(Link, LinkPermission.link_id == Link.id)
        .where(LinkPermission.user_id == user_id)
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


@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Clear login lockout for a user (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    redis = await get_redis()
    await redis.delete(f"{LOGIN_ATTEMPT_PREFIX}{user.username}")

    return {"message": "User unlocked successfully"}
