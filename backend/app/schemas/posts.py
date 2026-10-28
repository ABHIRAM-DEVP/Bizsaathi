"""Pydantic schemas for content generation and social posts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PostGenerateRequest(BaseModel):
    """Request to generate channel-specific marketing draft."""

    channel: Literal["instagram", "whatsapp_status", "facebook", "generic"] = "instagram"
    language: Literal["en", "hi", "mr"] = "en"


class PostPatchRequest(BaseModel):
    """Edit draft text, incrementing version and invalidating old claims."""

    text: str = Field(min_length=1, max_length=4000)


class ClaimCheckRequest(BaseModel):
    """Bind a claim check to the exact post version being reviewed."""

    version: int = Field(ge=1)


class EvidenceReference(BaseModel):
    id: UUID
    source_kind: str
    source_id: UUID
    source_version: int


class ClaimResponse(BaseModel):
    """Fact or opinion claim extracted from post."""

    id: UUID
    text: str
    kind: str
    verdict: str | None = None
    severity: str | None = None
    repair_suggestion: str | None = None


class ClaimCheckItemResponse(ClaimResponse):
    evidence: list[EvidenceReference] = Field(default_factory=list)


class ClaimCheckResponse(BaseModel):
    post_id: UUID
    version: int
    claims: list[ClaimCheckItemResponse]
    summary: dict[str, int]
    overall: Literal["pass", "fail", "needs_owner"]


class PostResponse(BaseModel):
    """Generated or edited post draft."""

    id: UUID
    business_id: UUID
    product_id: UUID
    channel: str
    language: str
    text: str
    version: int
    status: str
    provenance: dict[str, Any]
    claims: list[ClaimResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
