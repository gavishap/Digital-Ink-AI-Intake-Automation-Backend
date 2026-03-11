"""
Supabase Storage manager for document file operations.
Handles uploads/downloads to storage buckets.
"""

import logging
from pathlib import Path
from typing import Optional
from .supabase_client import get_supabase

logger = logging.getLogger(__name__)

BUCKET_ORIGINALS = "originals"
BUCKET_PAGES = "pages"
BUCKET_ANNOTATED = "annotated"
BUCKET_REPORTS = "reports"
BUCKET_TEMPLATES = "templates"


def upload_file(
    bucket: str,
    storage_path: str,
    file_data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    sb = get_supabase()
    file_options = {"content-type": content_type}
    try:
        sb.storage.from_(bucket).upload(
            path=storage_path,
            file=file_data,
            file_options=file_options,
        )
    except Exception as first_err:
        if "Duplicate" in str(first_err) or "already exists" in str(first_err):
            logger.info("File exists, updating: %s/%s", bucket, storage_path)
            try:
                sb.storage.from_(bucket).update(
                    path=storage_path,
                    file=file_data,
                    file_options=file_options,
                )
            except Exception as update_err:
                logger.error("Storage update also FAILED: %s/%s — %s", bucket, storage_path, update_err)
                raise
        else:
            logger.error("Storage upload FAILED: %s/%s — %s", bucket, storage_path, first_err)
            raise

    full_path = f"{bucket}/{storage_path}"
    logger.info("Storage upload OK: %s (%d bytes, %s)", full_path, len(file_data), content_type)
    return full_path


def upload_from_path(
    bucket: str,
    storage_path: str,
    local_path: Path,
    content_type: Optional[str] = None,
) -> str:
    if content_type is None:
        suffix = local_path.suffix.lower()
        content_type = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".json": "application/json",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }.get(suffix, "application/octet-stream")

    with open(local_path, "rb") as f:
        return upload_file(bucket, storage_path, f.read(), content_type)


def download_file(bucket: str, storage_path: str) -> bytes:
    sb = get_supabase()
    try:
        data = sb.storage.from_(bucket).download(storage_path)
        logger.info("Storage download OK: %s/%s", bucket, storage_path)
        return data
    except Exception as e:
        logger.error("Storage download FAILED: %s/%s — %s", bucket, storage_path, e)
        raise


def get_public_url(bucket: str, storage_path: str) -> str:
    sb = get_supabase()
    return sb.storage.from_(bucket).get_public_url(storage_path)


def get_signed_url(bucket: str, storage_path: str, expires_in: int = 3600) -> str:
    sb = get_supabase()
    result = sb.storage.from_(bucket).create_signed_url(storage_path, expires_in)
    return result["signedURL"]


def delete_file(bucket: str, storage_path: str) -> None:
    sb = get_supabase()
    try:
        sb.storage.from_(bucket).remove([storage_path])
        logger.info("Storage delete OK: %s/%s", bucket, storage_path)
    except Exception as e:
        logger.error("Storage delete FAILED: %s/%s — %s", bucket, storage_path, e)
        raise
