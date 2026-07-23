"""System settings management endpoints."""

from typing import Annotated, Callable, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SystemSettingUpdate, SystemSettingResponse
from app.api.deps import require_superuser
from app.services.audit import build_field_changes, record_audit_log


router = APIRouter()

PUBLIC_SETTING_KEYS = {
    "site_title", "login_title", "login_bg_image", "links_per_row",
    "copyright_info", "icp_number", "icp_link",
    "password_min_length", "password_require_uppercase",
    "password_require_lowercase", "password_require_digit",
    "password_require_special",
}


def _is_bool_string(value: str) -> bool:
    return value.lower() in {"true", "false"}


def _is_positive_int(value: str) -> bool:
    try:
        return int(value) > 0
    except ValueError:
        return False


# Keys with a semantically-typed value (int/bool) get validated before saving,
# so a malformed admin edit fails fast here instead of raising ValueError deep
# inside password validation / template rendering later.
SETTING_VALUE_VALIDATORS: dict[str, Callable[[str], bool]] = {
    "password_min_length": _is_positive_int,
    "password_require_uppercase": _is_bool_string,
    "password_require_lowercase": _is_bool_string,
    "password_require_digit": _is_bool_string,
    "password_require_special": _is_bool_string,
    "links_per_row": _is_positive_int,
    "max_login_attempts": _is_positive_int,
    "login_lockout_minutes": _is_positive_int,
    "audit_log_retention_days": _is_positive_int,
}


def _validate_setting_value(key: str, value: str) -> None:
    validator = SETTING_VALUE_VALIDATORS.get(key)
    if validator is not None and not validator(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value for setting '{key}'",
        )


@router.get("/public", response_model=List[SystemSettingResponse])
async def list_public_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[SystemSettingResponse]:
    """Get public settings (no auth required)."""
    stmt = select(SystemSetting).where(SystemSetting.key.in_(PUBLIC_SETTING_KEYS))
    result = await db.execute(stmt)
    settings = result.scalars().all()
    return [SystemSettingResponse.model_validate(s) for s in settings]


@router.get("/", response_model=List[SystemSettingResponse])
async def list_system_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> List[SystemSettingResponse]:
    """
    Get all system settings (admin only).

    Args:
        db: Database session
        current_user: Current active user

    Returns:
        List of all system settings
    """
    stmt = select(SystemSetting).order_by(SystemSetting.key)
    result = await db.execute(stmt)
    settings = result.scalars().all()

    return [SystemSettingResponse.model_validate(setting) for setting in settings]


@router.get("/{key}", response_model=SystemSettingResponse)
async def get_system_setting(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> SystemSettingResponse:
    """
    Get specific setting by key (admin only).

    Args:
        key: Setting key
        db: Database session
        current_user: Current active user

    Returns:
        System setting details

    Raises:
        HTTPException: If setting not found
    """
    stmt = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System setting not found",
        )

    return SystemSettingResponse.model_validate(setting)


@router.put("/{key}", response_model=SystemSettingResponse)
async def update_system_setting(
    key: str,
    setting_data: SystemSettingUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> SystemSettingResponse:
    """
    Update setting value (admin only).

    Args:
        key: Setting key
        setting_data: Setting update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated system setting

    Raises:
        HTTPException: If setting not found
    """
    stmt = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System setting not found",
        )

    _validate_setting_value(key, setting_data.value)

    field_changes = build_field_changes({"value": setting.value}, {"value": setting_data.value})
    if not field_changes:
        return SystemSettingResponse.model_validate(setting)

    setting.value = setting_data.value
    setting.updated_by = current_user.id

    await record_audit_log(
        db,
        user_id=current_user.id,
        action="setting.update",
        resource_type="system_setting",
        changes={"setting_key": key, "field_changes": field_changes},
        request=request,
    )
    await db.commit()
    await db.refresh(setting)

    return SystemSettingResponse.model_validate(setting)
