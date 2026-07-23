"""User management endpoints."""

import logging
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from redis.exceptions import RedisError
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
from app.core.navigation_access import build_group_path
from app.services.audit import build_field_changes, record_audit_log

logger = logging.getLogger(__name__)

LOGIN_ATTEMPT_PREFIX = "login_attempts:"


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1, max_length=100)


router = APIRouter()


async def _validate_user_group_ids(
    db: AsyncSession,
    group_ids: list[UUID],
) -> list[UUID]:
    unique_group_ids = list(dict.fromkeys(group_ids))
    if not unique_group_ids:
        return []

    stmt = select(UserGroup.id).where(UserGroup.id.in_(unique_group_ids))
    result = await db.execute(stmt)
    existing_ids = set(result.scalars().all())
    missing_ids = [str(gid) for gid in unique_group_ids if gid not in existing_ids]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User group not found: {', '.join(missing_ids)}",
        )
    return unique_group_ids


@router.get("/", response_model=List[UserResponse])
async def list_users(
    response: Response,
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
        List of users with lock status. Total matching count is returned via
        the X-Total-Count response header so callers can page through results.
    """
    count_result = await db.execute(select(func.count()).select_from(User))
    response.headers["X-Total-Count"] = str(count_result.scalar_one())

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

    lock_info: dict[str, tuple[int | None, int | None]] = {}
    try:
        redis = await get_redis()
        pipe = redis.pipeline()
        for user in users:
            attempt_key = f"{LOGIN_ATTEMPT_PREFIX}{user.username}"
            pipe.get(attempt_key)
            pipe.ttl(attempt_key)
        redis_results = await pipe.execute()
        for index, user in enumerate(users):
            attempts = redis_results[index * 2]
            ttl = redis_results[index * 2 + 1]
            lock_info[user.username] = (
                int(attempts) if attempts is not None else None,
                int(ttl) if ttl is not None else None,
            )
    except RedisError:
        logger.warning("Failed to fetch login lock info from Redis", exc_info=True)
        lock_info = {}

    user_responses = []
    for user in users:
        user_dict = UserResponse.model_validate(user).model_dump()
        attempts, ttl = lock_info.get(user.username, (None, None))
        if attempts is not None and attempts >= max_attempts:
            user_dict["is_locked"] = True
            if ttl and ttl > 0:
                from datetime import datetime, timedelta, timezone
                user_dict["locked_until"] = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        else:
            user_dict["is_locked"] = False
        user_responses.append(UserResponse(**user_dict))

    return user_responses


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
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
    stmt = select(User).where(
        or_(User.username == user_data.username, User.email == user_data.email)
    )
    result = await db.execute(stmt)
    existing_users = result.scalars().all()
    if any(user.username == user_data.username for user in existing_users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if any(user.email == user_data.email for user in existing_users):
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
    group_ids = await _validate_user_group_ids(
        db, list(user_data.user_group_ids) if user_data.user_group_ids else []
    )
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

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="create",
        resource_type="user",
        resource_id=new_user.id,
        changes={"username": new_user.username, "is_superuser": new_user.is_superuser},
        request=request,
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
    request: Request,
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

    original_username = user.username
    update_data = user_data.model_dump(exclude_unset=True, exclude={"user_group_ids"})
    current_values = {field: getattr(user, field) for field in update_data}
    field_changes = build_field_changes(current_values, update_data)

    current_group_ids = sorted(str(group.id) for group in user.user_groups)
    group_ids: list[UUID] | None = None
    if user_data.user_group_ids is not None:
        validated_group_ids = await _validate_user_group_ids(db, list(user_data.user_group_ids))
        new_group_ids = sorted(str(gid) for gid in validated_group_ids)
        if new_group_ids != current_group_ids:
            group_ids = validated_group_ids
            field_changes.append({
                "field": "user_group_ids",
                "old_value": current_group_ids,
                "new_value": new_group_ids,
            })

    if not field_changes:
        return UserResponse.model_validate(user)

    if group_ids is not None:
        await db.execute(
            user_group_members.delete().where(user_group_members.c.user_id == user_id)
        )
        if group_ids:
            await db.execute(
                user_group_members.insert(),
                [{"user_group_id": gid, "user_id": user_id} for gid in group_ids]
            )

    # Update user fields (immutable pattern)
    for field, value in update_data.items():
        setattr(user, field, value)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.update",
        resource_type="user",
        resource_id=user_id,
        changes={"username": original_username, "field_changes": field_changes},
        request=request,
    )
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
    request: Request,
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

    deleted_username = user.username
    await db.delete(user)
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.delete",
        resource_type="user",
        resource_id=user_id,
        changes={"username": deleted_username},
        request=request,
    )
    await db.commit()

    # Invalidate permissions cache
    await invalidate_user_permissions_cache(user_id)


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: UUID,
    body: ResetPasswordRequest,
    request: Request,
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
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.reset_password",
        resource_type="user",
        resource_id=user_id,
        changes={"username": user.username},
        request=request,
    )
    await db.commit()

    try:
        redis = await get_redis()
        await redis.delete(f"{LOGIN_ATTEMPT_PREFIX}{user.username}")
    except RedisError:
        logger.warning(
            "Failed to clear login attempt counter after password reset for user %s",
            user.username,
            exc_info=True,
        )

    return {"message": "Password reset successfully"}


@router.post("/{user_id}/disable", response_model=UserResponse)
async def disable_user(
    user_id: UUID,
    request: Request,
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
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.disable",
        resource_type="user",
        resource_id=user_id,
        changes={"username": user.username},
        request=request,
    )
    await db.commit()
    await invalidate_user_permissions_cache(user_id)

    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.user_groups))
    )
    return UserResponse.model_validate(result.scalar_one())


@router.post("/{user_id}/enable", response_model=UserResponse)
async def enable_user(
    user_id: UUID,
    request: Request,
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
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.enable",
        resource_type="user",
        resource_id=user_id,
        changes={"username": user.username},
        request=request,
    )
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
    request: Request,
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
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="user.unlock",
        resource_type="user",
        resource_id=user_id,
        changes={"username": user.username},
        request=request,
    )
    await db.commit()

    return {"message": "User unlocked successfully"}
