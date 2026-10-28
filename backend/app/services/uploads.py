"""Upload service enforcing media validation, tenant isolation, and presigned URLs."""

import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import PayloadTooLargeError, UnsupportedMediaError
from app.models.domain import Media
from app.schemas.uploads import UploadRequest, UploadResponse

# Allowed MIME types and extensions
PHOTO_MIMES = {"image/jpeg", "image/png", "image/webp"}
AUDIO_MIMES = {
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
    "audio/webm",
    "audio/x-m4a",
    "audio/aac",
}

ALLOWED_EXTENSIONS = {
    "photo": {".jpg", ".jpeg", ".png", ".webp"},
    "audio": {".mp3", ".wav", ".ogg", ".mp4", ".m4a", ".aac", ".webm"},
}

DISALLOWED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".bin",
    ".dll",
    ".py",
    ".js",
    ".html",
    ".php",
    ".com",
    ".scr",
}

# Size limits in bytes
MAX_PHOTO_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB


class UploadService:
    """Handles upload authorization, media validation, and presigned URL generation."""

    def __init__(self, session: Session | None = None):
        self._session = session

    def validate_upload(self, req: UploadRequest) -> str:
        """Validate media kind, mime type, size, and file extension.

        Returns normalized lowercase extension (e.g. '.jpg').
        """
        _, ext = os.path.splitext(req.filename.lower())

        if ext in DISALLOWED_EXTENSIONS:
            raise UnsupportedMediaError(f"Executable or dangerous extension '{ext}' is prohibited")

        if req.kind == "photo":
            if req.mime not in PHOTO_MIMES:
                raise UnsupportedMediaError(
                    f"Unsupported photo MIME '{req.mime}'. Allowed: {', '.join(sorted(PHOTO_MIMES))}"
                )
            if ext not in ALLOWED_EXTENSIONS["photo"]:
                raise UnsupportedMediaError(
                    f"Invalid photo extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS['photo']))}"
                )
            if req.size_bytes > MAX_PHOTO_BYTES:
                raise PayloadTooLargeError(
                    f"Photo size {req.size_bytes} bytes exceeds maximum limit of {MAX_PHOTO_BYTES} bytes (10MB)"
                )
        elif req.kind == "audio":
            if req.mime not in AUDIO_MIMES:
                raise UnsupportedMediaError(
                    f"Unsupported audio MIME '{req.mime}'. Allowed: {', '.join(sorted(AUDIO_MIMES))}"
                )
            if ext not in ALLOWED_EXTENSIONS["audio"]:
                raise UnsupportedMediaError(
                    f"Invalid audio extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS['audio']))}"
                )
            if req.size_bytes > MAX_AUDIO_BYTES:
                raise PayloadTooLargeError(
                    f"Audio size {req.size_bytes} bytes exceeds maximum limit of {MAX_AUDIO_BYTES} bytes (25MB)"
                )
        else:
            raise UnsupportedMediaError(f"Unsupported upload kind '{req.kind}'")

        return ext

    def generate_storage_key(self, business_id: UUID, media_id: UUID, ext: str) -> str:
        """Generate a tenant-prefixed collision-free storage path."""
        now = datetime.now(timezone.utc)
        return f"{business_id}/uploads/{now.year}/{now.month:02d}/{media_id}{ext}"

    def generate_presigned_url(self, storage_key: str, mime: str, expires_in: int = 900) -> str:
        """Generate presigned upload URL for direct storage upload."""
        # For dev/local/compose MinIO: direct S3-compatible PUT URL
        return f"http://localhost:9000/bizsaathi/{storage_key}?X-Amz-Expires={expires_in}&upload=direct"

    def create_upload_session(
        self,
        business_id: UUID,
        req: UploadRequest,
    ) -> UploadResponse:
        """Validate request, generate presigned URL, and record pending media."""
        ext = self.validate_upload(req)
        media_id = uuid4()
        storage_key = self.generate_storage_key(business_id, media_id, ext)
        upload_url = self.generate_presigned_url(storage_key, req.mime, expires_in=900)

        # Record media in DB if session provided
        if self._session is not None:
            media = Media(
                id=media_id,
                business_id=business_id,
                kind=req.kind,
                storage_key=storage_key,
                mime=req.mime,
                size_bytes=req.size_bytes,
                status="pending",
            )
            self._session.add(media)
            self._session.flush()

        return UploadResponse(
            media_id=media_id,
            upload_url=upload_url,
            storage_key=storage_key,
            expires_in_seconds=900,
            method="PUT",
        )
