"""Audit log recording helper.

Sensitive operations (user lifecycle, password resets, permission
grants/revokes) call this to persist an AuditLog row. The row is added to
the session but not explicitly committed here — it rides along with the
caller's own transaction and is flushed by the `get_db` dependency's
trailing commit, so a failed request never leaves an orphaned audit entry.
"""

from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.system_setting import SystemSetting
from app.utils.time import now_cst


def normalize_audit_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalize_audit_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_audit_value(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_audit_value(item) for item in value]
    return value


def build_field_changes(current: Mapping[str, Any], updates: Mapping[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for field, new_value in updates.items():
        old_value = current.get(field)
        if old_value != new_value:
            changes.append({
                "field": field,
                "old_value": normalize_audit_value(old_value),
                "new_value": normalize_audit_value(new_value),
            })
    return changes


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def get_audit_log_retention_days(db: AsyncSession) -> int:
    setting = await db.scalar(
        select(SystemSetting.value).where(SystemSetting.key == "audit_log_retention_days")
    )
    try:
        days = int(setting) if setting is not None else 30
    except (TypeError, ValueError):
        return 30
    return max(days, 1)


async def purge_expired_audit_logs(db: AsyncSession, retention_days: int | None = None) -> None:
    days = retention_days if retention_days is not None else await get_audit_log_retention_days(db)
    cutoff = now_cst() - timedelta(days=max(days, 1))
    await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))


async def record_audit_log(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    changes: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    """Queue an audit log entry for the current transaction."""
    await purge_expired_audit_logs(db)
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=normalize_audit_value(changes) if changes is not None else None,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(entry)
