"""Audit log read endpoints (admin only). Entries are written by app.services.audit;
this module is read-only by design so the audit trail can't be edited via the API."""

from datetime import datetime
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superuser
from app.config import settings
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit import purge_expired_audit_logs

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    action: str | None = Query(None, description="Filter by exact action, e.g. user.disable"),
    resource_type: str | None = Query(None),
    user_id: UUID | None = Query(None, description="Filter by the acting user"),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
) -> List[AuditLogResponse]:
    """
    List audit log entries (paginated, admin only).

    Total matching count is returned via the X-Total-Count response header.
    """
    await purge_expired_audit_logs(db)
    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if start_time:
        conditions.append(AuditLog.created_at >= start_time)
    if end_time:
        conditions.append(AuditLog.created_at <= end_time)

    count_stmt = select(func.count()).select_from(AuditLog)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
    count_result = await db.execute(count_stmt)
    response.headers["X-Total-Count"] = str(count_result.scalar_one())

    stmt = (
        select(AuditLog, User.username.label("username"))
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    for condition in conditions:
        stmt = stmt.where(condition)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        AuditLogResponse(
            id=row.AuditLog.id,
            user_id=row.AuditLog.user_id,
            username=row.username,
            action=row.AuditLog.action,
            resource_type=row.AuditLog.resource_type,
            resource_id=row.AuditLog.resource_id,
            changes=row.AuditLog.changes,
            ip_address=row.AuditLog.ip_address,
            user_agent=row.AuditLog.user_agent,
            created_at=row.AuditLog.created_at,
        )
        for row in rows
    ]
