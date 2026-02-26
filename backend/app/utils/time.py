"""Timezone utilities for consistent UTC+8 timestamps."""

from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    """Return current time in UTC+8, truncated to seconds (naive datetime)."""
    return datetime.now(CST).replace(tzinfo=None, microsecond=0)
