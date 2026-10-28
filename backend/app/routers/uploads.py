"""Uploads router for presigned direct-to-storage uploads."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.schemas.uploads import UploadRequest, UploadResponse
from app.services.uploads import UploadService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUpload",
    summary="Request a presigned direct upload URL (EP-U01)",
)
async def create_upload(
    req: UploadRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Validate asset metadata and return a presigned S3 upload URL."""
    service = UploadService(session=db)
    return service.create_upload_session(business_id=auth.business_id, req=req)
