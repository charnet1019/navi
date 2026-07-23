"""Shared CRUD helpers for fine-grained (link / navigation-group) permissions.

LinkPermission and NavigationGroupPermission share an identical shape
(a target foreign key, plus mutually-exclusive user_id / user_group_id,
plus granted_at / granted_by) and were previously implemented with
near-duplicate endpoint code. These helpers centralize that logic.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_group import UserGroup
from app.services.audit import record_audit_log


async def _principal_audit_names(
    db: AsyncSession,
    user_id: UUID | None,
    user_group_id: UUID | None,
) -> dict[str, str | None]:
    if user_id is not None:
        user = await db.get(User, user_id)
        return {"user_name": user.username if user else None}

    if user_group_id is not None:
        user_group = await db.get(UserGroup, user_group_id)
        return {"user_group_name": user_group.name if user_group else None}

    return {}


async def validate_grant_target(
    db: AsyncSession,
    user_id: UUID | None,
    user_group_id: UUID | None,
) -> None:
    """Ensure exactly one of user_id/user_group_id is provided and it exists."""
    if (user_id is None and user_group_id is None) or (user_id is not None and user_group_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly one of user_id or user_group_id",
        )

    if user_id:
        exists = (await db.execute(User.__table__.select().where(User.id == user_id))).first()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    else:
        exists = (await db.execute(UserGroup.__table__.select().where(UserGroup.id == user_group_id))).first()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User group not found")


async def grant_permission(
    db: AsyncSession,
    model: Any,
    target_column: Column,
    target_value: UUID | None,
    user_id: UUID | None,
    user_group_id: UUID | None,
    granted_by: UUID,
    request: Request | None = None,
    audit_changes: dict[str, Any] | None = None,
) -> Any:
    """Create a permission row for the given target, or raise 400 if it already exists."""
    dup_stmt = model.__table__.select().where(
        target_column == target_value,
        model.user_id == user_id if user_id else model.user_group_id == user_group_id,
    )
    if (await db.execute(dup_stmt)).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")

    permission = model(
        user_id=user_id,
        user_group_id=user_group_id,
        granted_by=granted_by,
        **{target_column.key: target_value},
    )
    db.add(permission)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists")

    audit_data = {
        "target_column": target_column.key,
        "target_value": str(target_value) if target_value else None,
        "user_id": str(user_id) if user_id else None,
        "user_group_id": str(user_group_id) if user_group_id else None,
        **await _principal_audit_names(db, user_id, user_group_id),
    }
    if audit_changes:
        audit_data.update(audit_changes)

    await record_audit_log(
        db,
        user_id=granted_by,
        action="permission.grant",
        resource_type=model.__tablename__,
        resource_id=permission.id,
        changes=audit_data,
        request=request,
    )
    await db.commit()
    await db.refresh(permission)
    return permission


async def revoke_permission(
    db: AsyncSession,
    model: Any,
    permission_id: UUID,
    target_column: Column,
    target_value: UUID | None,
    revoked_by: UUID,
    request: Request | None = None,
    audit_changes: dict[str, Any] | None = None,
) -> None:
    """Delete a permission row scoped to the given target, or raise 404."""
    stmt = model.__table__.select().where(
        model.id == permission_id,
        target_column == target_value,
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    permission = await db.get(model, permission_id)
    revoked_user_id = permission.user_id
    revoked_user_group_id = permission.user_group_id
    await db.delete(permission)
    audit_data = {
        "target_column": target_column.key,
        "target_value": str(target_value) if target_value else None,
        "user_id": str(revoked_user_id) if revoked_user_id else None,
        "user_group_id": str(revoked_user_group_id) if revoked_user_group_id else None,
        **await _principal_audit_names(db, revoked_user_id, revoked_user_group_id),
    }
    if audit_changes:
        audit_data.update(audit_changes)

    await record_audit_log(
        db,
        user_id=revoked_by,
        action="permission.revoke",
        resource_type=model.__tablename__,
        resource_id=permission_id,
        changes=audit_data,
        request=request,
    )
    await db.commit()


async def list_permissions_with_names(
    db: AsyncSession,
    model: Any,
    response_cls: Any,
    target_column: Column,
    target_value: UUID | None,
    extra_target_field: str,
) -> list[Any]:
    """Fetch permission rows for a target, joined with user/user_group display names."""
    from sqlalchemy import select

    stmt = (
        select(
            model,
            User.username.label("user_name"),
            UserGroup.name.label("user_group_name"),
        )
        .outerjoin(User, model.user_id == User.id)
        .outerjoin(UserGroup, model.user_group_id == UserGroup.id)
        .where(target_column == target_value)
        .order_by(model.granted_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        response_cls(
            id=row[0].id,
            user_id=row[0].user_id,
            user_group_id=row[0].user_group_id,
            user_name=row.user_name,
            user_group_name=row.user_group_name,
            granted_at=row[0].granted_at,
            granted_by=row[0].granted_by,
            **{extra_target_field: getattr(row[0], target_column.key)},
        )
        for row in rows
    ]
