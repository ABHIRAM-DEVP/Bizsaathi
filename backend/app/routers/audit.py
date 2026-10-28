"""Read-only tenant-scoped audit and sanitized job trace endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.tenancy import AuthContext, require_tenant
from app.models.base import get_db
from app.models.domain import AuditEvent, Job, JobEvent

router = APIRouter(tags=["audit"])


@router.get("/audit-log", operation_id="listAuditEvents")
async def list_audit_events(
    auth: AuthContext = Depends(require_tenant), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    events = (
        db.execute(
            select(AuditEvent)
            .where(AuditEvent.business_id == auth.business_id)
            .order_by(AuditEvent.at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": event.id,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "detail": event.detail,
            "at": event.at,
            "actor_type": event.actor_type,
        }
        for event in events
    ]


@router.get("/jobs/{job_id}/trace", operation_id="getJobTrace")
async def get_job_trace(
    job_id: UUID, auth: AuthContext = Depends(require_tenant), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    job = db.execute(select(Job).where(Job.id == job_id, Job.business_id == auth.business_id)).scalar_one_or_none()
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")
    events = (
        db.execute(
            select(JobEvent)
            .where(JobEvent.job_id == job_id, JobEvent.business_id == auth.business_id)
            .order_by(JobEvent.seq)
        )
        .scalars()
        .all()
    )
    return [
        {
            "seq": event.seq,
            "node": event.node,
            "event": event.event,
            "tool": event.tool,
            "evidence_ids": [str(value) for value in event.evidence_ids],
            "decision": event.decision,
            "retry": event.retry,
            "duration_ms": event.duration_ms,
            "error_code": event.error_code,
        }
        for event in events
    ]
