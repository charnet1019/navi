"""Shared helpers for navigation group and link access checks."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.associations import LinkPermission, NavigationGroupPermission, user_group_members
from app.models.link import Link
from app.models.navigation_group import NavigationGroup
from app.models.user import User


@dataclass(slots=True)
class NavigationAccessScope:
    has_all_access: bool
    direct_group_ids: set[UUID]
    direct_link_ids: set[UUID]
    visible_group_ids: set[UUID]


def accessible_link_condition(scope: "NavigationAccessScope"):
    """Build a WHERE clause matching links visible under the given access scope."""
    conditions = []
    if scope.visible_group_ids:
        conditions.append(Link.navigation_group_id.in_(scope.visible_group_ids))
    if scope.direct_link_ids:
        conditions.append(Link.id.in_(scope.direct_link_ids))
    return or_(*conditions) if conditions else false()


async def _user_group_ids(db: AsyncSession, user: User) -> list[UUID]:
    stmt = select(user_group_members.c.user_group_id).where(user_group_members.c.user_id == user.id)
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]


def _permission_filters(user: User, user_group_ids: list[UUID]):
    filters = [NavigationGroupPermission.user_id == user.id]
    if user_group_ids:
        filters.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))
    return filters


def _link_permission_filters(user: User, user_group_ids: list[UUID]):
    filters = [LinkPermission.user_id == user.id]
    if user_group_ids:
        filters.append(LinkPermission.user_group_id.in_(user_group_ids))
    return filters


async def has_all_navigation_access(db: AsyncSession, user: User, user_group_ids: list[UUID]) -> bool:
    if user.is_superuser:
        return True

    stmt = select(NavigationGroupPermission.id).where(
        NavigationGroupPermission.navigation_group_id.is_(None),
        or_(*_permission_filters(user, user_group_ids)),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_direct_navigation_group_ids(db: AsyncSession, user: User, user_group_ids: list[UUID]) -> set[UUID]:
    if user.is_superuser:
        return set()

    stmt = select(NavigationGroupPermission.navigation_group_id).where(
        NavigationGroupPermission.navigation_group_id.isnot(None),
        or_(*_permission_filters(user, user_group_ids)),
    )
    result = await db.execute(stmt)
    return {row[0] for row in result.fetchall()}


async def get_direct_link_ids(db: AsyncSession, user: User, user_group_ids: list[UUID]) -> set[UUID]:
    if user.is_superuser:
        return set()

    stmt = select(LinkPermission.link_id).where(or_(*_link_permission_filters(user, user_group_ids)))
    result = await db.execute(stmt)
    return {row[0] for row in result.fetchall()}


async def get_direct_link_group_ids(db: AsyncSession, user: User, user_group_ids: list[UUID]) -> set[UUID]:
    if user.is_superuser:
        return set()

    stmt = (
        select(Link.navigation_group_id)
        .join(LinkPermission, LinkPermission.link_id == Link.id)
        .where(or_(*_link_permission_filters(user, user_group_ids)))
        .distinct()
    )
    result = await db.execute(stmt)
    return {group_id for group_id in result.scalars().all() if group_id is not None}


async def get_active_navigation_groups(
    db: AsyncSession,
    limit: int | None = None,
) -> dict[UUID, NavigationGroup]:
    stmt = select(NavigationGroup).where(NavigationGroup.is_active == True)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return {group.id: group for group in result.scalars().all()}


def find_ancestors(
    group_id: UUID | None,
    groups_map: dict[UUID, NavigationGroup],
    max_depth: int | None = None,
    current_depth: int = 0,
    visited: set[UUID] | None = None,
) -> set[UUID]:
    if max_depth is None:
        max_depth = settings.MAX_HIERARCHY_DEPTH
    if visited is None:
        visited = set()
    if not group_id or current_depth >= max_depth or group_id in visited or group_id not in groups_map:
        return set()

    visited.add(group_id)
    ancestors: set[UUID] = set()
    current = groups_map.get(group_id)
    if current and current.parent_id:
        ancestors.add(current.parent_id)
        ancestors.update(
            find_ancestors(
                current.parent_id,
                groups_map,
                max_depth,
                current_depth + 1,
                visited,
            )
        )
    return ancestors


def find_descendants(
    group_id: UUID | None,
    groups_map: dict[UUID, NavigationGroup],
    max_depth: int | None = None,
    current_depth: int = 0,
    visited: set[UUID] | None = None,
) -> set[UUID]:
    if max_depth is None:
        max_depth = settings.MAX_HIERARCHY_DEPTH
    if visited is None:
        visited = set()
    if not group_id or current_depth >= max_depth or group_id in visited:
        return set()

    visited.add(group_id)
    descendants: set[UUID] = set()
    for gid, group in groups_map.items():
        if group.parent_id == group_id:
            descendants.add(gid)
            descendants.update(
                find_descendants(
                    gid,
                    groups_map,
                    max_depth,
                    current_depth + 1,
                    visited,
                )
            )
    return descendants


def build_group_path(
    group_id: UUID | None,
    groups_map: dict[UUID, NavigationGroup],
    max_depth: int | None = None,
) -> str:
    if group_id is None:
        return "全部"
    if max_depth is None:
        max_depth = settings.MAX_HIERARCHY_DEPTH

    path_parts: list[str] = []
    current = groups_map.get(group_id)
    visited: set[UUID] = set()
    depth = 0

    while current and depth < max_depth:
        if current.id in visited:
            break
        visited.add(current.id)
        path_parts.insert(0, current.name)
        current = groups_map.get(current.parent_id) if current.parent_id else None
        depth += 1

    return "/".join(path_parts) if path_parts else ""


async def build_navigation_access_scope(
    db: AsyncSession,
    user: User,
) -> NavigationAccessScope:
    if user.is_superuser:
        groups_map = await get_active_navigation_groups(db)
        return NavigationAccessScope(
            has_all_access=True,
            direct_group_ids=set(),
            direct_link_ids=set(),
            visible_group_ids=set(groups_map.keys()),
        )

    user_group_ids = await _user_group_ids(db, user)

    if await has_all_navigation_access(db, user, user_group_ids):
        groups_map = await get_active_navigation_groups(db)
        return NavigationAccessScope(
            has_all_access=True,
            direct_group_ids=set(),
            direct_link_ids=set(),
            visible_group_ids=set(groups_map.keys()),
        )

    direct_group_ids = await get_direct_navigation_group_ids(db, user, user_group_ids)
    direct_link_ids = await get_direct_link_ids(db, user, user_group_ids)
    direct_link_group_ids = await get_direct_link_group_ids(db, user, user_group_ids)
    groups_map = await get_active_navigation_groups(db, settings.MAX_NAVIGATION_GROUPS)

    seed_group_ids = set(direct_group_ids) | direct_link_group_ids
    visible_group_ids = set(seed_group_ids)
    for group_id in seed_group_ids:
        visible_group_ids.update(find_ancestors(group_id, groups_map))
        visible_group_ids.update(find_descendants(group_id, groups_map))

    return NavigationAccessScope(
        has_all_access=False,
        direct_group_ids=direct_group_ids,
        direct_link_ids=direct_link_ids,
        visible_group_ids=visible_group_ids,
    )

