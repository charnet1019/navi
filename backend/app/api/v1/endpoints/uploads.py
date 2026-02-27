"""File upload endpoints."""

import uuid
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.link import Link
from app.models.navigation_group import NavigationGroup
from app.models.system_setting import SystemSetting
from app.api.deps import require_superuser
from app.database import get_db
from app.config import settings


router = APIRouter()


@router.post("/images/")
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Upload image (admin only)."""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB",
        )

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": unique_filename,
        "url": f"/uploads/{unique_filename}",
        "size": len(content),
    }


@router.delete("/images/{filename}")
async def delete_image(
    filename: str,
    current_user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Delete uploaded image and clear DB references (admin only)."""
    safe_name = Path(filename).name
    url = f"/uploads/{safe_name}"

    # Delete file from disk
    file_path = Path(settings.UPLOAD_DIR) / safe_name
    if file_path.exists():
        file_path.unlink()

    # Clear references in links.icon_path
    await db.execute(
        update(Link).where(Link.icon_path == url).values(icon_path=None)
    )
    # Clear references in navigation_groups.icon
    await db.execute(
        update(NavigationGroup).where(NavigationGroup.icon == url).values(icon=None)
    )
    # Clear references in system_settings (e.g. login_bg_image)
    await db.execute(
        update(SystemSetting)
        .where(SystemSetting.value == url)
        .where(SystemSetting.key.in_({"login_bg_image"}))
        .values(value="")
    )
    await db.commit()

    return {"detail": "ok"}
