"""File handling utilities: validation, upload saving, hashing, sanitization."""

import hashlib
import os
import re
import uuid
from typing import Set

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
ALLOWED_IMAGE_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
ALLOWED_DOC_EXTENSIONS: Set[str] = {".pdf"}
ALLOWED_DOC_MIME_TYPES: Set[str] = {"application/pdf"}


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and shell injection.

    Replaces any character that is not alphanumeric, a period, an underscore,
    or a dash with an underscore.
    """
    base = os.path.basename(filename)
    sanitized = re.sub(r"[^\w.\-]", "_", base)
    return sanitized.strip("._") or "file"


async def validate_image_file(file: UploadFile) -> None:
    """Validate that an uploaded file is an acceptable image.

    Checks MIME type and file extension. Raises HTTPException on failure.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename.",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    if file.content_type and file.content_type.lower() not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{file.content_type}'.",
        )


async def save_upload(file: UploadFile, directory: str) -> str:
    """Save an UploadFile to disk securely with a unique prefix.

    Args:
        file: The uploaded file.
        directory: Destination directory path.

    Returns:
        The absolute path to the saved file.

    Raises:
        HTTPException: If file size exceeds the configured maximum.
    """
    os.makedirs(directory, exist_ok=True)

    clean_name = sanitize_filename(file.filename or "upload.bin")
    unique_name = f"{uuid.uuid4().hex[:8]}_{clean_name}"
    dest_path = os.path.join(directory, unique_name)

    max_bytes = settings.max_upload_size_bytes
    bytes_written = 0

    async with aiofiles.open(dest_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                # Cleanup partially written file
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
                )
            await out_file.write(chunk)

    await file.seek(0)
    return os.path.abspath(dest_path)


def generate_file_hash(file_path: str) -> str:
    """Compute the SHA-256 hash of a file for tamper-evidence.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Hex-encoded SHA-256 digest string.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
