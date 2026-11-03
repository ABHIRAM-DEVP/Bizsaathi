"""Upload service enforcing tenant isolation, signed URLs, and verified local media storage."""

import hashlib
import hmac
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import (
    ConfigurationError,
    NotFoundError,
    PayloadTooLargeError,
    UnauthenticatedError,
    UnsupportedMediaError,
)
from app.models.domain import Media, Product
from app.schemas.uploads import UploadRequest, UploadResponse

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
    ".exe", ".bat", ".cmd", ".sh", ".bin", ".dll", ".py", ".js", ".html", ".php", ".com", ".scr",
}
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_AUDIO_BYTES = 25 * 1024 * 1024


class UploadService:
    """Issue one-time tenant-scoped upload URLs and persist verified media."""

    def __init__(self, session: Session | None = None):
        self._session = session

    def validate_upload(self, req: UploadRequest) -> str:
        _, ext = os.path.splitext(req.filename.lower())
        if ext in DISALLOWED_EXTENSIONS:
            raise UnsupportedMediaError(f"Executable or dangerous extension '{ext}' is prohibited")
        allowed_mimes = PHOTO_MIMES if req.kind == "photo" else AUDIO_MIMES
        max_bytes = MAX_PHOTO_BYTES if req.kind == "photo" else MAX_AUDIO_BYTES
        if req.mime not in allowed_mimes:
            raise UnsupportedMediaError(f"Unsupported {req.kind} MIME '{req.mime}'.")
        if ext not in ALLOWED_EXTENSIONS[req.kind]:
            raise UnsupportedMediaError(f"Invalid {req.kind} extension '{ext}'.")
        if req.size_bytes > max_bytes:
            raise PayloadTooLargeError(f"Upload exceeds the {max_bytes}-byte limit.")
        return ext

    def generate_storage_key(self, business_id: UUID, media_id: UUID, ext: str) -> str:
        now = datetime.now(timezone.utc)
        return f"{business_id}/uploads/{now.year}/{now.month:02d}/{media_id}{ext}"

    @staticmethod
    def _token(media: Media, expires: int) -> str:
        secret = settings.SECRET_KEY.get_secret_value()
        message = f"{media.business_id}:{media.id}:{expires}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    def make_upload_url(self, *, base_url: str, media: Media) -> str:
        expires = int((datetime.now(timezone.utc) + timedelta(seconds=settings.SIGNED_URL_TTL_SECONDS)).timestamp())
        query = urlencode({"expires": expires, "token": self._token(media, expires)})
        return f"{base_url.rstrip('/')}{settings.API_PREFIX}/uploads/{media.id}/content?{query}"

    def verify_upload_token(self, media: Media, *, expires: int, token: str) -> None:
        now = int(datetime.now(timezone.utc).timestamp())
        if expires < now or expires > now + settings.SIGNED_URL_TTL_SECONDS:
            raise UnauthenticatedError(detail="Upload URL is expired or invalid.")
        if not hmac.compare_digest(self._token(media, expires), token):
            raise UnauthenticatedError(detail="Upload URL is expired or invalid.")

    def media_path(self, storage_key: str) -> Path:
        root = Path(settings.MEDIA_STORAGE_PATH).expanduser().resolve()
        target = (root / storage_key).resolve()
        if not target.is_relative_to(root):
            raise ConfigurationError("Invalid media storage key.")
        return target

    @staticmethod
    def verify_file_signature(kind: str, mime: str, header: bytes) -> bool:
        if kind == "photo":
            return (
                (mime == "image/jpeg" and header.startswith(b"\xff\xd8\xff"))
                or (mime == "image/png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
                or (mime == "image/webp" and len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP")
            )
        if mime == "audio/wav":
            return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"
        if mime == "audio/ogg":
            return header.startswith(b"OggS")
        if mime in {"audio/mp4", "audio/x-m4a"}:
            return len(header) >= 8 and header[4:8] == b"ftyp"
        if mime == "audio/webm":
            return header.startswith(b"\x1a\x45\xdf\xa3")
        if mime == "audio/aac":
            return header.startswith(b"\xff\xf1") or header.startswith(b"\xff\xf9")
        if mime == "audio/mpeg":
            return header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)
        return False

    def store_upload(self, media: Media, chunks) -> None:
        destination = self.media_path(media.storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        size = 0
        digest = hashlib.sha256()
        head = bytearray()
        maximum = MAX_PHOTO_BYTES if media.kind == "photo" else MAX_AUDIO_BYTES
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".upload-", delete=False) as temp:
                temp_name = temp.name
                for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > maximum or size > media.size_bytes:
                        raise PayloadTooLargeError("Uploaded file exceeds its declared or permitted size.")
                    if len(head) < 16:
                        head.extend(chunk[: 16 - len(head)])
                    digest.update(chunk)
                    temp.write(chunk)
            if size != media.size_bytes:
                raise UnsupportedMediaError("Uploaded file size does not match the declared size.")
            if not self.verify_file_signature(media.kind, media.mime, bytes(head)):
                raise UnsupportedMediaError("Uploaded bytes do not match the declared media type.")
            os.replace(temp_name, destination)
            media.sha256 = digest.hexdigest()
            media.status = "verified"
            if self._session is not None:
                self._session.flush()
        except Exception:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

    async def store_upload_async(self, media: Media, chunks) -> None:
        destination = self.media_path(media.storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        size = 0
        digest = hashlib.sha256()
        head = bytearray()
        maximum = MAX_PHOTO_BYTES if media.kind == "photo" else MAX_AUDIO_BYTES
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".upload-", delete=False) as temp:
                temp_name = temp.name
                async for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > maximum or size > media.size_bytes:
                        raise PayloadTooLargeError("Uploaded file exceeds its declared or permitted size.")
                    if len(head) < 16:
                        head.extend(chunk[: 16 - len(head)])
                    digest.update(chunk)
                    temp.write(chunk)
            if size != media.size_bytes:
                raise UnsupportedMediaError("Uploaded file size does not match the declared size.")
            if not self.verify_file_signature(media.kind, media.mime, bytes(head)):
                raise UnsupportedMediaError("Uploaded bytes do not match the declared media type.")
            os.replace(temp_name, destination)
            media.sha256 = digest.hexdigest()
            media.status = "verified"
            if self._session is not None:
                self._session.flush()
        except Exception:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
            raise

    def create_upload_session(self, *, business_id: UUID, req: UploadRequest, base_url: str) -> UploadResponse:
        if self._session is None:
            raise ConfigurationError("A database session is required to create an upload.")
        ext = self.validate_upload(req)
        if req.product_id is not None:
            product = self._session.execute(
                select(Product).where(Product.id == req.product_id, Product.business_id == business_id)
            ).scalar_one_or_none()
            if product is None:
                raise NotFoundError("Product not found for this tenant.")
        media_id = uuid4()
        media = Media(
            id=media_id,
            business_id=business_id,
            product_id=req.product_id,
            kind=req.kind,
            storage_key=self.generate_storage_key(business_id, media_id, ext),
            mime=req.mime,
            size_bytes=req.size_bytes,
            status="pending",
        )
        self._session.add(media)
        self._session.flush()
        return UploadResponse(
            media_id=media_id,
            upload_url=self.make_upload_url(base_url=base_url, media=media),
            storage_key=media.storage_key,
            expires_in_seconds=settings.SIGNED_URL_TTL_SECONDS,
            method="PUT",
        )
