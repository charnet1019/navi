"""Utility for deleting uploaded files from disk."""

from pathlib import Path
from app.config import settings


def delete_upload_file(url: str) -> None:
    """Delete an uploaded file by its URL path (e.g. /uploads/xxx.jpg)."""
    if not url or not url.startswith("/uploads/"):
        return
    filename = Path(url).name
    file_path = Path(settings.UPLOAD_DIR) / filename
    if file_path.exists():
        file_path.unlink()
