"""Navigation group management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.navigation_group import NavigationGroup
from app.models.link import Link
from app.models.associations import NavigationGroupPermission
from app.models.user_group import UserGroup
from app.schemas.navigation_group import (
    NavigationGroupCreate,
    NavigationGroupUpdate,
    NavigationGroupResponse,
)
from app.utils.files import delete_upload_file
from app.schemas.permission import (
    GrantPermissionRequest,
    NavGroupPermissionResponse,
)
from app.schemas.reorder import ReorderItem
from app.api.deps import require_superuser, get_current_active_user
from app.core.navigation_access import build_navigation_access_scope, find_descendants
from app.config import settings
from app.services.permissions import grant_permission, list_permissions_with_names, revoke_permission, validate_grant_target
from app.services.audit import build_field_changes, record_audit_log


router = APIRouter()


async def _validate_parent_id(
    db: AsyncSession,
    parent_id: UUID | None,
    group_id: UUID | None = None,
) -> None:
    if parent_id is None:
        return
    if group_id is not None and parent_id == group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Navigation group cannot be its own parent",
        )

    parent_result = await db.execute(
        select(NavigationGroup.id).where(NavigationGroup.id == parent_id)
    )
    if parent_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent navigation group not found",
        )

    if group_id is None:
        return

    all_groups_result = await db.execute(
        select(NavigationGroup).limit(settings.MAX_NAVIGATION_GROUPS)
    )
    all_groups = {group.id: group for group in all_groups_result.scalars().all()}
    if parent_id in find_descendants(group_id, all_groups):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Navigation group cannot be moved under its descendant",
        )


@router.get("/", response_model=List[NavigationGroupResponse])
async def list_navigation_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=settings.MAX_NAVIGATION_GROUPS),
) -> List[NavigationGroupResponse]:
    """List navigation groups (filtered by user permissions)."""
    conditions = [NavigationGroup.is_active == True]

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access:
            if not scope.visible_group_ids:
                return []
            conditions.append(NavigationGroup.id.in_(scope.visible_group_ids))

    stmt = (
        select(NavigationGroup)
        .where(*conditions)
        .offset(skip)
        .limit(limit)
        .order_by(NavigationGroup.sort_order, NavigationGroup.name)
    )
    result = await db.execute(stmt)
    groups = result.scalars().all()
    return [NavigationGroupResponse.model_validate(group) for group in groups]


@router.post("/", response_model=NavigationGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_navigation_group(
    group_data: NavigationGroupCreate,
    request: Request,
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
    await _validate_parent_id(db, group_data.parent_id)

    # Create new navigation group
    new_group = NavigationGroup(
        name=group_data.name,
        description=group_data.description,
        icon=group_data.icon,
        sort_order=group_data.sort_order,
        is_active=group_data.is_active,
        parent_id=group_data.parent_id,
        created_by=current_user.id,
    )

    db.add(new_group)
    await db.flush()
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="navigation_group.create",
        resource_type="navigation_group",
        resource_id=new_group.id,
        changes={
            "name": new_group.name,
            "parent_id": str(new_group.parent_id) if new_group.parent_id else None,
            "is_active": new_group.is_active,
            "sort_order": new_group.sort_order,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(new_group)

    return NavigationGroupResponse.model_validate(new_group)


@router.put("/reorder", response_model=List[NavigationGroupResponse])
async def reorder_navigation_groups(
    items: List[ReorderItem],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[NavigationGroupResponse]:
    """Batch update sort order for navigation groups (admin only)."""
    if not items:
        return []

    requested_ids = [item.id for item in items]
    if len(set(requested_ids)) != len(requested_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate navigation group id in reorder request",
        )
    stmt = select(NavigationGroup).where(NavigationGroup.id.in_(requested_ids))
    result = await db.execute(stmt)
    groups_map = {group.id: group for group in result.scalars().all()}
    missing_ids = [str(group_id) for group_id in requested_ids if group_id not in groups_map]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Navigation group not found: {', '.join(missing_ids)}",
        )

    reorder_items = []
    for item in items:
        group = groups_map[item.id]
        if group.sort_order != item.sort_order:
            reorder_items.append({
                "id": str(item.id),
                "name": group.name,
                "old_sort_order": group.sort_order,
                "new_sort_order": item.sort_order,
            })
        group.sort_order = item.sort_order

    if reorder_items:
        await record_audit_log(
            db,
            user_id=current_user.id,
            action="navigation_group.reorder",
            resource_type="navigation_group",
            changes={"items": reorder_items},
            request=request,
        )
    await db.commit()

    return [NavigationGroupResponse.model_validate(groups_map[item.id]) for item in items]


@router.get("/all-permissions", response_model=List[NavGroupPermissionResponse])
async def list_all_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[NavGroupPermissionResponse]:
    """List 'all' permissions (navigation_group_id IS NULL) (admin only)."""
    return await list_permissions_with_names(
        db,
        NavigationGroupPermission,
        NavGroupPermissionResponse,
        NavigationGroupPermission.navigation_group_id,
        None,
        extra_target_field="navigation_group_id",
    )


@router.post("/all-permissions", status_code=status.HTTP_201_CREATED)
async def grant_all_permission(
    body: GrantPermissionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Grant 'all' navigation group access for user or user_group (admin only)."""
    user_id = body.user_id
    user_group_id = body.user_group_id

    await validate_grant_target(db, user_id, user_group_id)

    permission = await grant_permission(
        db,
        NavigationGroupPermission,
        NavigationGroupPermission.navigation_group_id,
        None,
        user_id,
        user_group_id,
        current_user.id,
        request=request,
        audit_changes={"target_name": "全部导航分组"},
    )

    return {"message": "Permission granted successfully", "permission_id": str(permission.id)}


@router.delete("/all-permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_permission(
    permission_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """Revoke 'all' navigation group access (admin only)."""
    await revoke_permission(
        db,
        NavigationGroupPermission,
        permission_id,
        NavigationGroupPermission.navigation_group_id,
        None,
        revoked_by=current_user.id,
        request=request,
        audit_changes={"target_name": "全部导航分组"},
    )


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

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access and group_id not in scope.visible_group_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Navigation group not found",
            )

    return NavigationGroupResponse.model_validate(group)


@router.put("/{group_id}", response_model=NavigationGroupResponse)
async def update_navigation_group(
    group_id: UUID,
    group_data: NavigationGroupUpdate,
    request: Request,
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

    original_group_name = group.name
    # Update group fields (immutable pattern)
    update_data = group_data.model_dump(exclude_unset=True)
    if "parent_id" in update_data:
        await _validate_parent_id(db, update_data["parent_id"], group_id)
    field_changes = build_field_changes(
        {
            "name": group.name,
            "description": group.description,
            "icon": group.icon,
            "sort_order": group.sort_order,
            "is_active": group.is_active,
            "parent_id": group.parent_id,
        },
        update_data,
    )
    if not field_changes:
        return NavigationGroupResponse.model_validate(group)

    for field, value in update_data.items():
        setattr(group, field, value)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="navigation_group.update",
        resource_type="navigation_group",
        resource_id=group_id,
        changes={"group_name": original_group_name, "field_changes": field_changes},
        request=request,
    )
    await db.commit()
    await db.refresh(group)

    return NavigationGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_navigation_group(
    group_id: UUID,
    request: Request,
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

    # Delete group icon file
    delete_upload_file(group.icon)

    # Delete icon files for all links in this group
    links_stmt = select(Link).where(Link.navigation_group_id == group_id)
    links_result = await db.execute(links_stmt)
    deleted_link_ids = []
    for link in links_result.scalars():
        deleted_link_ids.append(str(link.id))
        delete_upload_file(link.icon_path)

    deleted_group = {
        "name": group.name,
        "parent_id": str(group.parent_id) if group.parent_id else None,
        "deleted_link_ids": deleted_link_ids,
    }
    await db.delete(group)
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="navigation_group.delete",
        resource_type="navigation_group",
        resource_id=group_id,
        changes=deleted_group,
        request=request,
    )
    await db.commit()


@router.put("/{group_id}/sort-order", response_model=NavigationGroupResponse)
async def update_navigation_group_sort_order(
    group_id: UUID,
    request: Request,
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

    old_sort_order = group.sort_order
    group.sort_order = sort_order
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="navigation_group.sort_order_update",
        resource_type="navigation_group",
        resource_id=group_id,
        changes={
            "group_name": group.name,
            "field_changes": [
                {"field": "sort_order", "old_value": old_sort_order, "new_value": sort_order}
            ],
        },
        request=request,
    )
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

    return await list_permissions_with_names(
        db,
        NavigationGroupPermission,
        NavGroupPermissionResponse,
        NavigationGroupPermission.navigation_group_id,
        group_id,
        extra_target_field="navigation_group_id",
    )


@router.post("/{group_id}/permissions", status_code=status.HTTP_201_CREATED)
async def grant_navigation_group_permission(
    group_id: UUID,
    body: GrantPermissionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Grant access to navigation group for user or user_group (admin only)."""
    user_id = body.user_id
    user_group_id = body.user_group_id

    await validate_grant_target(db, user_id, user_group_id)

    # Verify navigation group exists
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    permission = await grant_permission(
        db,
        NavigationGroupPermission,
        NavigationGroupPermission.navigation_group_id,
        group_id,
        user_id,
        user_group_id,
        current_user.id,
        request=request,
        audit_changes={"target_name": group.name},
    )

    return {
        "message": "Permission granted successfully",
        "permission_id": str(permission.id),
    }


@router.delete("/{group_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_navigation_group_permission(
    group_id: UUID,
    permission_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """Revoke access to navigation group (admin only)."""
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Navigation group not found")

    await revoke_permission(
        db,
        NavigationGroupPermission,
        permission_id,
        NavigationGroupPermission.navigation_group_id,
        group_id,
        revoked_by=current_user.id,
        request=request,
        audit_changes={"target_name": group.name},
    )

