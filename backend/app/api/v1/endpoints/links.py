"""Link management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.link import Link
from app.models.navigation_group import NavigationGroup
from app.models.associations import LinkPermission, NavigationGroupPermission
from app.models.user_group import UserGroup
from app.schemas.link import LinkCreate, LinkUpdate, LinkResponse
from app.schemas.permission import GrantPermissionRequest, LinkPermissionResponse
from app.api.deps import require_superuser, get_current_active_user
from app.config import settings
from app.utils.files import delete_upload_file


router = APIRouter()


@router.get("/", response_model=List[LinkResponse])
async def list_links(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    navigation_group_id: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> List[LinkResponse]:
    """
    List links (filtered by user permissions).

    Args:
        db: Database session
        current_user: Current active user
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of links the user has access to
    """
    if current_user.is_superuser:
        conditions = [Link.is_active == (is_active if is_active is not None else True)]
        if navigation_group_id:
            conditions.append(Link.navigation_group_id == navigation_group_id)
        stmt = select(Link).where(*conditions).offset(skip).limit(limit).order_by(
            Link.sort_order, Link.name
        )
    else:
        user_group_ids = [ug.id for ug in current_user.user_groups]
        nav_filter = [NavigationGroupPermission.user_id == current_user.id]
        link_filter = [LinkPermission.user_id == current_user.id]
        if user_group_ids:
            nav_filter.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))
            link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))

        # Check for "all" nav-group permission (navigation_group_id IS NULL)
        all_perm_stmt = select(NavigationGroupPermission).where(
            NavigationGroupPermission.navigation_group_id.is_(None),
            or_(*nav_filter),
        )
        all_perm = await db.execute(all_perm_stmt)
        has_all_access = all_perm.scalar_one_or_none() is not None

        if has_all_access:
            conditions = [Link.is_active == True]
            if navigation_group_id:
                conditions.append(Link.navigation_group_id == navigation_group_id)
            if is_active is not None:
                conditions[0] = Link.is_active == is_active
            stmt = select(Link).where(*conditions).offset(skip).limit(limit).order_by(
                Link.sort_order, Link.name
            )
        else:
            # Get directly permitted group IDs
            permitted_group_ids_stmt = select(
                NavigationGroupPermission.navigation_group_id
            ).where(
                NavigationGroupPermission.navigation_group_id.isnot(None),
                or_(*nav_filter),
            )
            permitted_result = await db.execute(permitted_group_ids_stmt)
            permitted_group_ids = set(permitted_result.scalars().all())

            # If user has group permissions, expand to include descendants
            if permitted_group_ids:
                # Fetch all active navigation groups with limit
                all_groups_stmt = select(NavigationGroup).where(
                    NavigationGroup.is_active == True
                ).limit(settings.MAX_NAVIGATION_GROUPS)
                all_groups_result = await db.execute(all_groups_stmt)
                all_groups = {g.id: g for g in all_groups_result.scalars().all()}

                # Find all descendants of permitted groups
                def find_descendants(group_id, groups_map, max_depth=None, current_depth=0, visited=None):
                    """Recursively find all descendant group IDs with depth limit and cycle detection."""
                    if max_depth is None:
                        max_depth = settings.MAX_HIERARCHY_DEPTH
                    if visited is None:
                        visited = set()
                    if not group_id or current_depth >= max_depth or group_id in visited:
                        return set()
                    visited.add(group_id)

                    descendants = set()
                    for gid, group in groups_map.items():
                        if group.parent_id == group_id:
                            descendants.add(gid)
                            descendants.update(find_descendants(gid, groups_map, max_depth, current_depth + 1, visited))
                    return descendants

                # Expand permitted groups to include descendants
                expanded_group_ids = set(permitted_group_ids)
                for group_id in permitted_group_ids:
                    if group_id:  # Input validation
                        expanded_group_ids.update(find_descendants(group_id, all_groups))

                permitted_group_ids = expanded_group_ids

            direct_link_ids_stmt = select(
                LinkPermission.link_id
            ).where(or_(*link_filter))

            # Build base conditions
            active_condition = Link.is_active == (is_active if is_active is not None else True)
            perm_condition = or_(
                Link.navigation_group_id.in_(permitted_group_ids) if permitted_group_ids else False,
                Link.id.in_(direct_link_ids_stmt),
            )
            conditions = [active_condition, perm_condition]
            if navigation_group_id:
                conditions.append(Link.navigation_group_id == navigation_group_id)

            stmt = select(Link).where(*conditions).offset(skip).limit(limit).order_by(
                Link.sort_order, Link.name
            )

    result = await db.execute(stmt)
    links = result.scalars().all()

    return [LinkResponse.model_validate(link) for link in links]


@router.post("/", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_data: LinkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> LinkResponse:
    """
    Create link (admin only).

    Args:
        link_data: Link creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created link

    Raises:
        HTTPException: If navigation group not found
    """
    # Verify navigation group exists
    stmt = select(NavigationGroup).where(NavigationGroup.id == link_data.navigation_group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    # Create new link
    new_link = Link(
        name=link_data.name,
        description=link_data.description,
        url=link_data.url,
        icon_path=link_data.icon_path,
        navigation_group_id=link_data.navigation_group_id,
        sort_order=link_data.sort_order,
        is_active=link_data.is_active,
        open_in_new_tab=link_data.open_in_new_tab,
        created_by=current_user.id,
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)

    return LinkResponse.model_validate(new_link)


class ReorderItem(BaseModel):
    id: UUID
    sort_order: int


@router.put("/reorder", response_model=List[LinkResponse])
async def reorder_links(
    items: List[ReorderItem],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[LinkResponse]:
    """Batch update sort order for links (admin only)."""
    stmt = select(Link).where(Link.id.in_([item.id for item in items]))
    result = await db.execute(stmt)
    links_map = {l.id: l for l in result.scalars().all()}

    for item in items:
        link = links_map.get(item.id)
        if link:
            link.sort_order = item.sort_order

    await db.commit()

    updated = []
    for item in items:
        link = links_map.get(item.id)
        if link:
            await db.refresh(link)
            updated.append(LinkResponse.model_validate(link))
    return updated


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> LinkResponse:
    """
    Get link details (if user has access).

    Args:
        link_id: Link ID
        db: Database session
        current_user: Current active user

    Returns:
        Link details

    Raises:
        HTTPException: If link not found or user doesn't have access
    """
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    # Permission check for non-superusers
    if not current_user.is_superuser:
        user_group_ids = [ug.id for ug in current_user.user_groups]
        nav_filter = [NavigationGroupPermission.user_id == current_user.id]
        link_filter = [LinkPermission.user_id == current_user.id]
        if user_group_ids:
            nav_filter.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))
            link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))

        # Check "all" nav-group permission
        all_perm_stmt = select(NavigationGroupPermission).where(
            NavigationGroupPermission.navigation_group_id.is_(None),
            or_(*nav_filter),
        )
        all_perm = await db.execute(all_perm_stmt)
        has_all_access = all_perm.scalar_one_or_none() is not None

        if not has_all_access:
            # Get all permitted group IDs
            permitted_ids_stmt = select(
                NavigationGroupPermission.navigation_group_id
            ).where(
                NavigationGroupPermission.navigation_group_id.isnot(None),
                or_(*nav_filter),
            )
            permitted_result = await db.execute(permitted_ids_stmt)
            permitted_group_ids = set(permitted_result.scalars().all())

            # Check if user has direct permission to link's group
            has_group_access = link.navigation_group_id in permitted_group_ids

            # If not, check if user has permission to any ancestor
            if not has_group_access and permitted_group_ids and link.navigation_group_id:
                # Fetch all groups to find ancestors with limit
                all_groups_stmt = select(NavigationGroup).where(
                    NavigationGroup.is_active == True
                ).limit(settings.MAX_NAVIGATION_GROUPS)
                all_groups_result = await db.execute(all_groups_stmt)
                all_groups = {g.id: g for g in all_groups_result.scalars().all()}

                # Find ancestors of the link's group
                def find_ancestors(gid, groups_map, max_depth=None, current_depth=0, visited=None):
                    """Recursively find all ancestor group IDs with depth limit and cycle detection."""
                    if max_depth is None:
                        max_depth = settings.MAX_HIERARCHY_DEPTH
                    if visited is None:
                        visited = set()
                    if not gid or current_depth >= max_depth or gid in visited or gid not in groups_map:
                        return set()
                    visited.add(gid)

                    ancestors = set()
                    current = groups_map.get(gid)
                    if current and current.parent_id:
                        ancestors.add(current.parent_id)
                        ancestors.update(find_ancestors(current.parent_id, groups_map, max_depth, current_depth + 1, visited))
                    return ancestors

                ancestor_ids = find_ancestors(link.navigation_group_id, all_groups)
                # User has access if they have permission to any ancestor
                has_group_access = bool(permitted_group_ids & ancestor_ids)

            if not has_group_access:
                # Check direct link permission
                link_perm_stmt = select(LinkPermission).where(
                    LinkPermission.link_id == link_id,
                    or_(*link_filter),
                )
                link_perm = await db.execute(link_perm_stmt)
                if link_perm.scalar_one_or_none() is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Link not found",
                    )

    return LinkResponse.model_validate(link)


@router.put("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: UUID,
    link_data: LinkUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> LinkResponse:
    """
    Update link (admin only).

    Args:
        link_id: Link ID
        link_data: Link update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated link

    Raises:
        HTTPException: If link not found or navigation group not found
    """
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    # Verify navigation group exists if being changed
    if link_data.navigation_group_id:
        stmt = select(NavigationGroup).where(NavigationGroup.id == link_data.navigation_group_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Navigation group not found",
            )

    # Update link fields (immutable pattern)
    update_data = link_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(link, field, value)

    await db.commit()
    await db.refresh(link)

    return LinkResponse.model_validate(link)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Delete link (admin only).

    Args:
        link_id: Link ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If link not found
    """
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    delete_upload_file(link.icon_path)
    await db.delete(link)
    await db.commit()


@router.put("/{link_id}/sort-order", response_model=LinkResponse)
async def update_link_sort_order(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    sort_order: int = Query(..., ge=0),
) -> LinkResponse:
    """
    Update link sort order (admin only).

    Args:
        link_id: Link ID
        sort_order: New sort order
        db: Database session
        current_user: Current superuser

    Returns:
        Updated link

    Raises:
        HTTPException: If link not found
    """
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    link.sort_order = sort_order
    await db.commit()
    await db.refresh(link)

    return LinkResponse.model_validate(link)


@router.get("/{link_id}/permissions", response_model=List[LinkPermissionResponse])
async def list_link_permissions(
    link_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[LinkPermissionResponse]:
    """List permissions for a link (admin only)."""
    # Verify link exists
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    stmt = (
        select(
            LinkPermission,
            User.username.label("user_name"),
            UserGroup.name.label("user_group_name"),
        )
        .outerjoin(User, LinkPermission.user_id == User.id)
        .outerjoin(UserGroup, LinkPermission.user_group_id == UserGroup.id)
        .where(LinkPermission.link_id == link_id)
        .order_by(LinkPermission.granted_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        LinkPermissionResponse(
            id=row.LinkPermission.id,
            link_id=row.LinkPermission.link_id,
            user_id=row.LinkPermission.user_id,
            user_group_id=row.LinkPermission.user_group_id,
            user_name=row.user_name,
            user_group_name=row.user_group_name,
            granted_at=row.LinkPermission.granted_at,
            granted_by=row.LinkPermission.granted_by,
        )
        for row in rows
    ]


@router.post("/{link_id}/permissions", status_code=status.HTTP_201_CREATED)
async def grant_link_permission(
    link_id: UUID,
    body: GrantPermissionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """
    Grant access to link for user or user_group (admin only).

    Args:
        link_id: Link ID
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

    # Verify link exists
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
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
    stmt = select(LinkPermission).where(
        LinkPermission.link_id == link_id,
        LinkPermission.user_id == user_id if user_id else LinkPermission.user_group_id == user_group_id,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists",
        )

    # Create permission
    permission = LinkPermission(
        link_id=link_id,
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


@router.delete("/{link_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_link_permission(
    link_id: UUID,
    permission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Revoke access to link (admin only).

    Args:
        link_id: Link ID
        permission_id: Permission ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If permission not found
    """
    stmt = select(LinkPermission).where(
        LinkPermission.id == permission_id,
        LinkPermission.link_id == link_id,
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


@router.get("/by-group/{group_id}", response_model=List[LinkResponse])
async def get_links_by_navigation_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[LinkResponse]:
    """
    Get links by navigation group (filtered by user permissions).

    Args:
        group_id: Navigation group ID
        db: Database session
        current_user: Current active user

    Returns:
        List of links in the navigation group that user has access to

    Raises:
        HTTPException: If navigation group not found
    """
    # Verify navigation group exists
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    if current_user.is_superuser:
        stmt = select(Link).where(
            Link.navigation_group_id == group_id,
            Link.is_active == True,
        ).order_by(Link.sort_order, Link.name)
    else:
        user_group_ids = [ug.id for ug in current_user.user_groups]
        nav_filter = [NavigationGroupPermission.user_id == current_user.id]
        link_filter = [LinkPermission.user_id == current_user.id]
        if user_group_ids:
            nav_filter.append(NavigationGroupPermission.user_group_id.in_(user_group_ids))
            link_filter.append(LinkPermission.user_group_id.in_(user_group_ids))

        # Check if user has "all" permission
        all_perm_stmt = select(NavigationGroupPermission).where(
            NavigationGroupPermission.navigation_group_id.is_(None),
            or_(*nav_filter),
        )
        all_perm_result = await db.execute(all_perm_stmt)
        has_all_access = all_perm_result.scalar_one_or_none() is not None

        if has_all_access:
            has_group_access = True
        else:
            # Get all permitted group IDs
            permitted_ids_stmt = select(
                NavigationGroupPermission.navigation_group_id
            ).where(
                NavigationGroupPermission.navigation_group_id.isnot(None),
                or_(*nav_filter),
            )
            permitted_result = await db.execute(permitted_ids_stmt)
            permitted_group_ids = set(permitted_result.scalars().all())

            # Check if user has direct permission to this group
            has_group_access = group_id in permitted_group_ids

            # If not, check if user has permission to any ancestor
            if not has_group_access and permitted_group_ids and group_id:
                # Fetch the requested group and its ancestors with limit
                all_groups_stmt = select(NavigationGroup).where(
                    NavigationGroup.is_active == True
                ).limit(settings.MAX_NAVIGATION_GROUPS)
                all_groups_result = await db.execute(all_groups_stmt)
                all_groups = {g.id: g for g in all_groups_result.scalars().all()}

                # Find ancestors of the requested group
                def find_ancestors(gid, groups_map, max_depth=None, current_depth=0, visited=None):
                    """Recursively find all ancestor group IDs with depth limit and cycle detection."""
                    if max_depth is None:
                        max_depth = settings.MAX_HIERARCHY_DEPTH
                    if visited is None:
                        visited = set()
                    if not gid or current_depth >= max_depth or gid in visited or gid not in groups_map:
                        return set()
                    visited.add(gid)

                    ancestors = set()
                    current = groups_map.get(gid)
                    if current and current.parent_id:
                        ancestors.add(current.parent_id)
                        ancestors.update(find_ancestors(current.parent_id, groups_map, max_depth, current_depth + 1, visited))
                    return ancestors

                ancestor_ids = find_ancestors(group_id, all_groups)
                # User has access if they have permission to any ancestor
                has_group_access = bool(permitted_group_ids & ancestor_ids)

        if has_group_access:
            stmt = select(Link).where(
                Link.navigation_group_id == group_id,
                Link.is_active == True,
            ).order_by(Link.sort_order, Link.name)
        else:
            # Only show directly permitted links in this group
            direct_link_ids_stmt = select(
                LinkPermission.link_id
            ).where(or_(*link_filter))
            stmt = select(Link).where(
                Link.navigation_group_id == group_id,
                Link.is_active == True,
                Link.id.in_(direct_link_ids_stmt),
            ).order_by(Link.sort_order, Link.name)

    result = await db.execute(stmt)
    links = result.scalars().all()

    return [LinkResponse.model_validate(link) for link in links]


