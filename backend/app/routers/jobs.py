"""Jobs router for async background task status tracking."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.tenancy import AuthContext, require_tenant
from app.models.base import get_db
from app.models.domain import Job
from app.schemas.jobs import JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getJob",
    summary="Get background job status (EP-J01)",
)
async def get_job(
    job_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Retrieve async job progress and outcome within tenant scope."""
    stmt = select(Job).where(
        Job.id == job_id,
        Job.business_id == auth.business_id,
    )
    job = db.execute(stmt).scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")

    return JobResponse(
        id=job.id,
        business_id=job.business_id,
        kind=job.kind,
        status=job.status,
        progress_step=job.progress_step,
        progress_total=job.progress_total,
        result_ref=job.result_ref,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
