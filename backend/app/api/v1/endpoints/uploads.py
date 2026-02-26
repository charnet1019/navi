"""File upload endpoints."""

import os
import uuid
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse

from app.models.user import User
from app.api.deps import require_superuser
from app.config import settings


router = APIRouter()


@router.post("/images/")
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(require_superuser)],
) -> dict:
    """
    Upload image for link icon (admin only).

    Args:
        file: Image file to upload
        current_user: Current superuser

    Returns:
        Upload details including filename, path, and URL

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file exists
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}",
        )

    # Read file content to validate size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(content)

    # Return upload details
    return {
        "filename": unique_filename,
        "url": f"/uploads/{unique_filename}",
        "size": len(content),
    }
