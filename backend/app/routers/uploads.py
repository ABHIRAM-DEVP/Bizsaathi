"""Tenant-scoped signed media upload and retrieval routes."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnauthenticatedError, UnsupportedMediaError
from app.core.tenancy import AuthContext, require_owner_role, require_tenant
from app.models.base import get_db
from app.models.domain import Media, Product
from app.schemas.uploads import UploadRequest, UploadResponse
from app.services.uploads import UploadService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUpload",
    summary="Request a signed direct upload URL (EP-U01)",
)
async def create_upload(
    req: UploadRequest,
    request: Request,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> UploadResponse:
    return UploadService(session=db).create_upload_session(
        business_id=auth.business_id,
        req=req,
        base_url=str(request.base_url),
    )


@router.put(
    "/{media_id}/content",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="putUploadContent",
    summary="Store media bytes using a short-lived signed URL",
)
async def put_upload_content(
    media_id: UUID,
    request: Request,
    expires: int = Query(ge=1),
    token: str = Query(min_length=64, max_length=64),
    db: Session = Depends(get_db),
) -> None:
    service = UploadService(session=db)
    media = db.execute(select(Media).where(Media.id == media_id)).scalar_one_or_none()
    if media is None:
        raise NotFoundError("Upload not found.")
    service.verify_upload_token(media, expires=expires, token=token)
    if media.status != "pending":
        raise UnauthenticatedError(detail="Upload URL has already been used.")

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != media.mime:
        raise UnsupportedMediaError("Upload content type does not match the declared media type.")

    await service.store_upload_async(media, request.stream())


@router.get(
    "/products/{product_id}/image",
    response_class=FileResponse,
    operation_id="getProductImage",
    summary="Get the tenant-scoped verified product image",
)
async def get_product_image(
    product_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> FileResponse:
    product = db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == auth.business_id)
    ).scalar_one_or_none()
    if product is None:
        raise NotFoundError("Product not found.")
    media = (
        db.execute(
            select(Media)
            .where(
                Media.business_id == auth.business_id,
                Media.product_id == product_id,
                Media.kind == "photo",
                Media.status == "verified",
            )
            .order_by(Media.created_at.desc())
        )
        .scalars()
        .first()
    )
    if media is None:
        raise NotFoundError("No verified product image is available.")
    file_path = UploadService().media_path(media.storage_key)
    if not file_path.is_file():
        raise NotFoundError("Stored product image is unavailable.")
    return FileResponse(
        Path(file_path),
        media_type=media.mime,
        filename=file_path.name,
        headers={"Cache-Control": "private, no-store"},
    )
