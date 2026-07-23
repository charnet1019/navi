"""Link management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.link import Link
from app.models.navigation_group import NavigationGroup
from app.models.associations import LinkPermission
from app.models.user_group import UserGroup
from app.schemas.link import LinkCreate, LinkUpdate, LinkResponse
from app.schemas.permission import GrantPermissionRequest, LinkPermissionResponse
from app.schemas.reorder import ReorderItem
from app.api.deps import require_superuser, get_current_active_user
from app.core.navigation_access import NavigationAccessScope, accessible_link_condition, build_navigation_access_scope
from app.config import settings
from app.services.permissions import grant_permission, list_permissions_with_names, revoke_permission, validate_grant_target
from app.services.audit import build_field_changes, record_audit_log
from app.utils.files import delete_upload_file


router = APIRouter()


def _parse_navigation_group_id(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid navigation group ID",
        )


@router.get("/", response_model=List[LinkResponse])
async def list_links(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=settings.MAX_NAVIGATION_GROUPS),
    navigation_group_id: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> List[LinkResponse]:
    """List links (filtered by user permissions)."""
    selected_group_id = _parse_navigation_group_id(navigation_group_id)
    active_condition = Link.is_active == (is_active if is_active is not None else True)
    conditions = [active_condition]
    if selected_group_id:
        conditions.append(Link.navigation_group_id == selected_group_id)

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access:
            conditions.append(accessible_link_condition(scope))

    stmt = (
        select(Link)
        .where(*conditions)
        .offset(skip)
        .limit(limit)
        .order_by(Link.sort_order, Link.name)
    )
    result = await db.execute(stmt)
    return [LinkResponse.model_validate(link) for link in result.scalars().all()]


@router.post("/", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_data: LinkCreate,
    request: Request,
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
    await db.flush()
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="link.create",
        resource_type="link",
        resource_id=new_link.id,
        changes={
            "name": new_link.name,
            "url": new_link.url,
            "navigation_group_id": str(new_link.navigation_group_id),
            "is_active": new_link.is_active,
        },
        request=request,
    )
    await db.commit()
    await db.refresh(new_link)

    return LinkResponse.model_validate(new_link)


@router.put("/reorder", response_model=List[LinkResponse])
async def reorder_links(
    items: List[ReorderItem],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[LinkResponse]:
    """Batch update sort order for links (admin only)."""
    if not items:
        return []

    requested_ids = [item.id for item in items]
    if len(set(requested_ids)) != len(requested_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate link id in reorder request",
        )
    stmt = select(Link).where(Link.id.in_(requested_ids))
    result = await db.execute(stmt)
    links_map = {link.id: link for link in result.scalars().all()}
    missing_ids = [str(link_id) for link_id in requested_ids if link_id not in links_map]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Link not found: {', '.join(missing_ids)}",
        )

    reorder_items = []
    for item in items:
        link = links_map[item.id]
        if link.sort_order != item.sort_order:
            reorder_items.append({
                "id": str(item.id),
                "name": link.name,
                "old_sort_order": link.sort_order,
                "new_sort_order": item.sort_order,
            })
        link.sort_order = item.sort_order

    if reorder_items:
        await record_audit_log(
            db,
            user_id=current_user.id,
            action="link.reorder",
            resource_type="link",
            changes={"items": reorder_items},
            request=request,
        )
    await db.commit()

    return [LinkResponse.model_validate(links_map[item.id]) for item in items]


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

    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if (
            not scope.has_all_access
            and link.navigation_group_id not in scope.visible_group_ids
            and link.id not in scope.direct_link_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found",
            )

    return LinkResponse.model_validate(link)


@router.put("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: UUID,
    link_data: LinkUpdate,
    request: Request,
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

    original_link_name = link.name
    # Update link fields (immutable pattern)
    update_data = link_data.model_dump(exclude_unset=True)
    field_changes = build_field_changes(
        {
            "name": link.name,
            "description": link.description,
            "url": link.url,
            "icon_path": link.icon_path,
            "navigation_group_id": link.navigation_group_id,
            "sort_order": link.sort_order,
            "is_active": link.is_active,
            "open_in_new_tab": link.open_in_new_tab,
        },
        update_data,
    )
    if not field_changes:
        return LinkResponse.model_validate(link)

    for field, value in update_data.items():
        setattr(link, field, value)

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="link.update",
        resource_type="link",
        resource_id=link_id,
        changes={"link_name": original_link_name, "field_changes": field_changes},
        request=request,
    )
    await db.commit()
    await db.refresh(link)

    return LinkResponse.model_validate(link)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: UUID,
    request: Request,
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
    deleted_link = {
        "name": link.name,
        "url": link.url,
        "navigation_group_id": str(link.navigation_group_id),
    }
    await db.delete(link)
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="link.delete",
        resource_type="link",
        resource_id=link_id,
        changes=deleted_link,
        request=request,
    )
    await db.commit()


@router.put("/{link_id}/sort-order", response_model=LinkResponse)
async def update_link_sort_order(
    link_id: UUID,
    request: Request,
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

    old_sort_order = link.sort_order
    link.sort_order = sort_order
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="link.sort_order_update",
        resource_type="link",
        resource_id=link_id,
        changes={
            "link_name": link.name,
            "field_changes": [
                {"field": "sort_order", "old_value": old_sort_order, "new_value": sort_order}
            ],
        },
        request=request,
    )
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

    return await list_permissions_with_names(
        db,
        LinkPermission,
        LinkPermissionResponse,
        LinkPermission.link_id,
        link_id,
        extra_target_field="link_id",
    )


@router.post("/{link_id}/permissions", status_code=status.HTTP_201_CREATED)
async def grant_link_permission(
    link_id: UUID,
    body: GrantPermissionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Grant access to link for user or user_group (admin only)."""
    user_id = body.user_id
    user_group_id = body.user_group_id

    await validate_grant_target(db, user_id, user_group_id)

    # Verify link exists
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    permission = await grant_permission(
        db,
        LinkPermission,
        LinkPermission.link_id,
        link_id,
        user_id,
        user_group_id,
        current_user.id,
        request=request,
        audit_changes={"target_name": link.name},
    )

    return {
        "message": "Permission granted successfully",
        "permission_id": str(permission.id),
    }


@router.delete("/{link_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_link_permission(
    link_id: UUID,
    permission_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """Revoke access to link (admin only)."""
    stmt = select(Link).where(Link.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    await revoke_permission(
        db, LinkPermission, permission_id, LinkPermission.link_id, link_id,
        revoked_by=current_user.id, request=request, audit_changes={"target_name": link.name},
    )


@router.get("/by-group/{group_id}", response_model=List[LinkResponse])
async def get_links_by_navigation_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[LinkResponse]:
    """Get links by navigation group (filtered by user permissions)."""
    stmt = select(NavigationGroup).where(NavigationGroup.id == group_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Navigation group not found",
        )

    conditions = [Link.navigation_group_id == group_id, Link.is_active == True]
    if not current_user.is_superuser:
        scope = await build_navigation_access_scope(db, current_user)
        if not scope.has_all_access and group_id not in scope.visible_group_ids:
            conditions.append(Link.id.in_(scope.direct_link_ids) if scope.direct_link_ids else false())

    stmt = select(Link).where(*conditions).order_by(Link.sort_order, Link.name)
    result = await db.execute(stmt)
    return [LinkResponse.model_validate(link) for link in result.scalars().all()]

