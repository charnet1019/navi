"""Role management endpoints."""

from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse, RoleWithPermissions
from app.api.deps import require_superuser
from app.models.user import User
from app.config import settings
from app.core.permissions import invalidate_user_permissions_cache


router = APIRouter()


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> List[RoleResponse]:
    """
    List roles (paginated, admin only).

    Args:
        db: Database session
        current_user: Current superuser
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of roles
    """
    stmt = select(Role).offset(skip).limit(limit).order_by(Role.created_at.desc())
    result = await db.execute(stmt)
    roles = result.scalars().all()

    return [RoleResponse.model_validate(role) for role in roles]


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> RoleResponse:
    """
    Create role (admin only).

    Args:
        role_data: Role creation data
        db: Database session
        current_user: Current superuser

    Returns:
        Created role

    Raises:
        HTTPException: If role name already exists
    """
    # Check if role name already exists
    stmt = select(Role).where(Role.name == role_data.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists",
        )

    # Create new role
    new_role = Role(
        name=role_data.name,
        description=role_data.description,
        is_system=False,  # User-created roles are never system roles
    )

    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)

    return RoleResponse.model_validate(new_role)


@router.get("/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> RoleWithPermissions:
    """
    Get role details with permissions (admin only).

    Args:
        role_id: Role ID
        db: Database session
        current_user: Current superuser

    Returns:
        Role details with permissions

    Raises:
        HTTPException: If role not found
    """
    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return RoleWithPermissions.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> RoleResponse:
    """
    Update role (admin only).

    Args:
        role_id: Role ID
        role_data: Role update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated role

    Raises:
        HTTPException: If role not found, is system role, or name already exists
    """
    stmt = select(Role).where(Role.id == role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Prevent modification of system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles",
        )

    # Check if name is being changed and already exists
    if role_data.name and role_data.name != role.name:
        stmt = select(Role).where(Role.name == role_data.name)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists",
            )

    # Update role fields
    update_data = role_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    await db.commit()
    await db.refresh(role)

    # Invalidate cache for all users with this role
    await _invalidate_role_users_cache(role_id, db)

    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> None:
    """
    Delete role (admin only, prevent system role deletion).

    Args:
        role_id: Role ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If role not found or is system role
    """
    stmt = select(Role).where(Role.id == role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Prevent deletion of system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles",
        )

    # Invalidate cache for all users with this role before deletion
    await _invalidate_role_users_cache(role_id, db)

    await db.delete(role)
    await db.commit()


@router.post("/{role_id}/permissions", response_model=RoleWithPermissions)
async def assign_permissions_to_role(
    role_id: UUID,
    permission_ids: List[UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> RoleWithPermissions:
    """
    Assign permissions to role (admin only).

    Args:
        role_id: Role ID
        permission_ids: List of permission IDs to assign
        db: Database session
        current_user: Current superuser

    Returns:
        Updated role with permissions

    Raises:
        HTTPException: If role not found, is system role, or permissions not found
    """
    # Fetch role with permissions
    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Prevent modification of system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles",
        )

    # Fetch permissions
    stmt = select(Permission).where(Permission.id.in_(permission_ids))
    result = await db.execute(stmt)
    permissions = result.scalars().all()

    if len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more permissions not found",
        )

    # Add permissions to role (avoid duplicates)
    existing_permission_ids = {p.id for p in role.permissions}
    for permission in permissions:
        if permission.id not in existing_permission_ids:
            role.permissions.append(permission)

    await db.commit()
    await db.refresh(role)

    # Invalidate cache for all users with this role
    await _invalidate_role_users_cache(role_id, db)

    return RoleWithPermissions.model_validate(role)


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleWithPermissions)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> RoleWithPermissions:
    """
    Remove permission from role (admin only).

    Args:
        role_id: Role ID
        permission_id: Permission ID to remove
        db: Database session
        current_user: Current superuser

    Returns:
        Updated role with permissions

    Raises:
        HTTPException: If role not found, is system role, or permission not found
    """
    # Fetch role with permissions
    stmt = (
        select(Role)
        .where(Role.id == role_id)
        .options(selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Prevent modification of system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles",
        )

    # Find and remove permission
    permission_to_remove = None
    for permission in role.permissions:
        if permission.id == permission_id:
            permission_to_remove = permission
            break

    if permission_to_remove is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not assigned to this role",
        )

    role.permissions.remove(permission_to_remove)

    await db.commit()
    await db.refresh(role)

    # Invalidate cache for all users with this role
    await _invalidate_role_users_cache(role_id, db)

    return RoleWithPermissions.model_validate(role)


async def _invalidate_role_users_cache(role_id: UUID, db: AsyncSession) -> None:
    """
    Invalidate permissions cache for all users with a specific role.

    Args:
        role_id: Role ID
        db: Database session
    """
    # Fetch all users with this role
    stmt = (
        select(User)
        .join(User.roles)
        .where(Role.id == role_id)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Invalidate cache for each user
    for user in users:
        await invalidate_user_permissions_cache(user.id)
