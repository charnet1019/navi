"""File upload endpoints."""

import io
import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_superuser
from app.config import settings
from app.database import get_db
from app.models.link import Link
from app.models.navigation_group import NavigationGroup
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.services.audit import record_audit_log


router = APIRouter()

MAX_IMAGE_PIXELS = 40_000_000  # ~40MP cap to guard against decompression bombs

UPLOAD_CHUNK_SIZE = 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES: dict[str, set[str]] = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".jfif": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".ico": {"image/x-icon", "image/vnd.microsoft.icon"},
    ".bmp": {"image/bmp", "image/x-ms-bmp"},
    ".tif": {"image/tiff"},
    ".tiff": {"image/tiff"},
    ".avif": {"image/avif"},
}


def _has_valid_image_signature(file_ext: str, header: bytes) -> bool:
    if file_ext in {".jpg", ".jpeg", ".jfif"}:
        return header.startswith(b"\xff\xd8\xff")
    if file_ext == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if file_ext == ".gif":
        return header.startswith((b"GIF87a", b"GIF89a"))
    if file_ext == ".webp":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if file_ext == ".ico":
        return header.startswith(b"\x00\x00\x01\x00")
    if file_ext == ".bmp":
        return header.startswith(b"BM")
    if file_ext in {".tif", ".tiff"}:
        return header.startswith((b"II*\x00", b"MM\x00*"))
    if file_ext == ".avif":
        return len(header) >= 16 and header[4:8] == b"ftyp" and b"avif" in header[8:32]
    return False


def _validate_upload_metadata(file: UploadFile, file_ext: str) -> None:
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(settings.ALLOWED_IMAGE_EXTENSIONS))}",
        )

    content_type = (file.content_type or "").split(";", 1)[0].lower()
    allowed_mimes = ALLOWED_IMAGE_MIME_TYPES.get(file_ext, set())
    if content_type and content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file content type",
        )


def _validate_image_payload(data: bytes) -> None:
    """Decode the full image with Pillow to reject corrupt/malicious payloads."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions too large",
                )
            img.verify()
    except HTTPException:
        raise
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image content",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image",
        )


@router.post("/images/")
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """Upload image (admin only)."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    file_ext = Path(file.filename).suffix.lower()
    _validate_upload_metadata(file, file_ext)

    buffer = bytearray()
    chunk = await file.read(UPLOAD_CHUNK_SIZE)
    while chunk:
        buffer.extend(chunk)
        if len(buffer) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB",
            )
        chunk = await file.read(UPLOAD_CHUNK_SIZE)

    if not buffer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    if not _has_valid_image_signature(file_ext, bytes(buffer[:64])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image content",
        )
    _validate_image_payload(bytes(buffer))

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename

    total_size = len(buffer)
    try:
        async with aiofiles.open(file_path, "wb") as output:
            await output.write(buffer)
    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    url = f"/uploads/{unique_filename}"
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="upload.image_create",
        resource_type="upload",
        changes={
            "filename": unique_filename,
            "url": url,
            "size": total_size,
            "content_type": file.content_type,
        },
        request=request,
    )
    await db.commit()

    return {
        "filename": unique_filename,
        "url": url,
        "size": total_size,
    }


@router.delete("/images/{filename}")
async def delete_image(
    filename: str,
    request: Request,
    current_user: Annotated[User, Depends(require_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Delete uploaded image and clear DB references (admin only)."""
    safe_name = Path(filename).name
    file_ext = Path(safe_name).suffix.lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type",
        )
    url = f"/uploads/{safe_name}"

    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    file_path = (upload_dir / safe_name).resolve()
    if file_path.parent != upload_dir:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    is_referenced = any(
        (
            (await db.execute(select(Link.id).where(Link.icon_path == url).limit(1))).first(),
            (await db.execute(select(NavigationGroup.id).where(NavigationGroup.icon == url).limit(1))).first(),
            (
                await db.execute(
                    select(SystemSetting.key)
                    .where(SystemSetting.value == url)
                    .where(SystemSetting.key.in_({"login_bg_image"}))
                    .limit(1)
                )
            ).first(),
        )
    )
    if not is_referenced:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image is not referenced by any record",
        )

    if file_path.exists():
        file_path.unlink()

    await db.execute(
        update(Link).where(Link.icon_path == url).values(icon_path=None)
    )
    await db.execute(
        update(NavigationGroup).where(NavigationGroup.icon == url).values(icon=None)
    )
    await db.execute(
        update(SystemSetting)
        .where(SystemSetting.value == url)
        .where(SystemSetting.key.in_({"login_bg_image"}))
        .values(value="")
    )
    await record_audit_log(
        db,
        user_id=current_user.id,
        action="upload.image_delete",
        resource_type="upload",
        changes={"filename": safe_name, "url": url},
        request=request,
    )
    await db.commit()

    return {"detail": "ok"}
