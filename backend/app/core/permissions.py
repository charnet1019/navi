"""Permission checking utilities with Redis caching."""

import json
import logging
from typing import Set
from uuid import UUID
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.redis import get_redis

logger = logging.getLogger(__name__)

PERMISSION_CACHE_TTL = 300  # 5 minutes


async def get_user_permissions(
    user_id: UUID,
    db: AsyncSession,
) -> Set[str]:
    """
    Get all permissions for a user (with Redis caching).

    Permissions are aggregated from:
    - User's direct roles

    Args:
        user_id: User ID to get permissions for
        db: Database session

    Returns:
        Set of permission names (format: "resource:action")
    """
    # Try to get from cache first
    redis = await get_redis()
    cache_key = f"user_permissions:{user_id}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return set(json.loads(cached))
    except (RedisError, json.JSONDecodeError):
        # Don't fail if Redis is unavailable or cache entry is corrupted
        logger.warning("Redis permission cache read failed for user %s", user_id, exc_info=True)

    # Fetch from database
    permissions = await _fetch_user_permissions_from_db(user_id, db)

    # Cache the result
    try:
        await redis.setex(
            cache_key,
            PERMISSION_CACHE_TTL,
            json.dumps(list(permissions))
        )
    except RedisError:
        logger.warning("Redis permission cache write failed for user %s", user_id, exc_info=True)

    return permissions


async def _fetch_user_permissions_from_db(
    user_id: UUID,
    db: AsyncSession,
) -> Set[str]:
    """
    Fetch user permissions from database.

    Args:
        user_id: User ID to get permissions for
        db: Database session

    Returns:
        Set of permission names (format: "resource:action")
    """
    # Fetch user with roles and permissions eagerly loaded
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return set()

    permissions = set()

    # Add permissions from user's direct roles
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(f"{permission.resource}:{permission.action}")

    return permissions


async def check_permission(
    user_id: UUID,
    resource: str,
    action: str,
    db: AsyncSession,
) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user_id: User ID to check
        resource: Resource name (e.g., "users", "links")
        action: Action name (e.g., "read", "write", "delete")
        db: Database session

    Returns:
        True if user has permission, False otherwise
    """
    permissions = await get_user_permissions(user_id, db)
    permission_key = f"{resource}:{action}"
    return permission_key in permissions


async def invalidate_user_permissions_cache(user_id: UUID) -> None:
    """
    Clear Redis cache for user permissions.

    Call this when user roles or permissions change.

    Args:
        user_id: User ID to invalidate cache for
    """
    redis = await get_redis()
    cache_key = f"user_permissions:{user_id}"

    try:
        await redis.delete(cache_key)
    except RedisError:
        logger.warning("Redis permission cache invalidation failed for user %s", user_id, exc_info=True)
