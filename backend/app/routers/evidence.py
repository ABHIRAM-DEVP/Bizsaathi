"""Tenant-safe evidence lookup for claim verification (EP-J02)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.tenancy import AuthContext, require_tenant
from app.models.base import get_db
from app.models.domain import Evidence
from app.schemas.posts import EvidenceReference

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get(
    "/{evidence_id}",
    status_code=status.HTTP_200_OK,
    operation_id="getEvidence",
    summary="Get a tenant-scoped redacted evidence snapshot (EP-J02)",
)
async def get_evidence(
    evidence_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    evidence = db.execute(
        select(Evidence).where(Evidence.id == evidence_id, Evidence.business_id == auth.business_id)
    ).scalar_one_or_none()
    if not evidence:
        raise NotFoundError(f"Evidence {evidence_id} not found.")
    reference = EvidenceReference(
        id=evidence.id,
        source_kind=evidence.source_kind,
        source_id=evidence.source_id,
        source_version=evidence.source_version,
    )
    return {**reference.model_dump(), "snapshot": evidence.snapshot}
