"""Upload schemas for photo and audio asset onboarding."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

UploadKind = Literal["photo", "audio"]


class UploadRequest(BaseModel):
    """Request payload to request a presigned upload URL."""

    kind: UploadKind = Field(description="Media type: photo or audio")
    filename: str = Field(min_length=1, max_length=255, description="Client filename including extension")
    mime: str = Field(min_length=3, max_length=100, description="MIME content-type")
    size_bytes: int = Field(gt=0, description="File size in bytes")


class UploadResponse(BaseModel):
    """Presigned upload URL and registered media record details."""

    media_id: UUID = Field(description="Created media record ID")
    upload_url: str = Field(description="Presigned PUT URL for direct-to-storage upload")
    storage_key: str = Field(description="Tenant-prefixed collision-free storage path")
    expires_in_seconds: int = Field(default=900, description="Validity period of upload URL in seconds")
    method: str = Field(default="PUT", description="HTTP method for uploading")
