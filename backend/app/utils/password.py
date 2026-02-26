"""Password validation utility based on system settings."""

import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting


# Default values matching system settings defaults
DEFAULTS = {
    "password_min_length": 6,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digit": True,
    "password_require_special": True,
}


async def _get_password_settings(db: AsyncSession) -> dict:
    """Load password rule settings from database."""
    keys = list(DEFAULTS.keys())
    stmt = select(SystemSetting).where(SystemSetting.key.in_(keys))
    result = await db.execute(stmt)
    rows = {s.key: s.value for s in result.scalars().all()}

    return {
        "min_length": int(rows.get("password_min_length", DEFAULTS["password_min_length"])),
        "require_uppercase": rows.get("password_require_uppercase", "true").lower() == "true",
        "require_lowercase": rows.get("password_require_lowercase", "true").lower() == "true",
        "require_digit": rows.get("password_require_digit", "true").lower() == "true",
        "require_special": rows.get("password_require_special", "true").lower() == "true",
    }


async def validate_password(password: str, db: AsyncSession) -> list[str]:
    """
    Validate password against configured rules.

    Returns a list of error messages. Empty list means valid.
    """
    rules = await _get_password_settings(db)
    errors: list[str] = []

    if len(password) < rules["min_length"]:
        errors.append(f"密码长度不能少于{rules['min_length']}个字符")

    if rules["require_uppercase"] and not re.search(r"[A-Z]", password):
        errors.append("密码必须包含大写字母")

    if rules["require_lowercase"] and not re.search(r"[a-z]", password):
        errors.append("密码必须包含小写字母")

    if rules["require_digit"] and not re.search(r"\d", password):
        errors.append("密码必须包含数字")

    if rules["require_special"] and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        errors.append("密码必须包含特殊字符")

    return errors
