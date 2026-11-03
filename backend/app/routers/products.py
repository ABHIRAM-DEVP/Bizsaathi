"""Products router implementing catalogue CRUD, intake triggers, and stock adjustments."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.models import InputBundle
from app.agents.runner import AgentJobRunner
from app.core.errors import (
    ConflictError,
    EvidenceMissingError,
    IdempotencyConflictError,
    NotFoundError,
    StaleVersionError,
)
from app.core.errors import ValidationError as DomainValidationError
from app.core.logging import logger
from app.core.tenancy import AuthContext, require_owner_role, require_tenant
from app.models.base import get_db, get_session
from app.models.domain import Job, Media, Product, ProductVariant, Proposal
from app.repositories.product import ProductRepository
from app.repositories.variant import VariantRepository
from app.schemas.products import (
    ProductCreateRequest,
    ProductFromPhotoRequest,
    ProductFromVoiceRequest,
    ProductPatchRequest,
    ProductResponse,
    ProductStockAdjustmentRequest,
)

router = APIRouter(prefix="/products", tags=["products"])


async def _run_agent_bg(business_id: UUID, job_id: UUID, input_bundle: InputBundle) -> None:
    """Run an agent job in its own transaction so request teardown cannot roll it back."""
    db = get_session()
    try:
        runner = AgentJobRunner(session=db, business_id=business_id)
        try:
            await runner.run_job(job_id=job_id, input_bundle=input_bundle)
        except Exception as exc:
            db.commit()
            logger.error(
                "Background agent job failed",
                extra={
                    "business_id": str(business_id),
                    "job_id": str(job_id),
                    "error_code": type(exc).__name__,
                },
            )
        else:
            db.commit()
    finally:
        db.close()


@router.post(
    "/from-photo",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="createProductFromPhoto",
    summary="Trigger product draft extraction from uploaded photos (EP-B02)",
)
async def create_product_from_photo(
    req: ProductFromPhotoRequest,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(require_owner_role),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Validate photo uploads and enqueue async draft extraction job."""
    # 1. Idempotency check
    if idempotency_key:
        stmt_idem = select(Job).where(
            Job.business_id == auth.business_id,
            Job.idempotency_key == idempotency_key,
        )
        existing_job = db.execute(stmt_idem).scalar_one_or_none()
        if existing_job:
            # Check if body media_ids match
            req_ids_set = {str(m) for m in req.media_ids}
            job_media_ids = existing_job.result_ref.get("media_ids", []) if existing_job.result_ref else []
            if job_media_ids and set(job_media_ids) != req_ids_set:
                raise IdempotencyConflictError("Idempotency-Key was already used with a different request body.")
            return {
                "job_id": str(existing_job.id),
                "status": existing_job.status,
                "poll_url": f"/v1/jobs/{existing_job.id}",
            }

    # 2. Verify all referenced media IDs belong to this tenant
    storage_keys: list[str] = []
    for media_id in req.media_ids:
        stmt_m = select(Media).where(
            Media.id == media_id,
            Media.business_id == auth.business_id,
        )
        media = db.execute(stmt_m).scalar_one_or_none()
        if not media:
            raise NotFoundError(f"Media asset {media_id} not found for this tenant.")
        storage_keys.append(media.storage_key)

    # 3. Create Job row
    job_id = uuid4()
    job = Job(
        id=job_id,
        business_id=auth.business_id,
        kind="product_from_photo",
        status="queued",
        idempotency_key=idempotency_key,
        result_ref={"media_ids": [str(m) for m in req.media_ids]},
    )
    db.add(job)
    db.flush()

    input_bundle = InputBundle(
        kind="product_from_photo",
        media_ids=req.media_ids,
        storage_keys=storage_keys,
    )
    db.commit()
    background_tasks.add_task(_run_agent_bg, auth.business_id, job_id, input_bundle)

    return {
        "job_id": str(job_id),
        "status": "queued",
        "poll_url": f"/v1/jobs/{job_id}",
    }


@router.post(
    "/from-voice",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="createProductFromVoice",
    summary="Trigger product draft extraction from voice recording (EP-B03)",
)
async def create_product_from_voice(
    req: ProductFromVoiceRequest,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Validate voice upload and enqueue audio transcription job."""
    stmt_m = select(Media).where(
        Media.id == req.media_id,
        Media.business_id == auth.business_id,
    )
    media = db.execute(stmt_m).scalar_one_or_none()
    if not media:
        raise NotFoundError(f"Media asset {req.media_id} not found.")

    job_id = uuid4()
    job = Job(
        id=job_id,
        business_id=auth.business_id,
        kind="product_from_voice",
        status="queued",
    )
    db.add(job)
    db.flush()

    input_bundle = InputBundle(
        kind="product_from_voice",
        media_ids=[req.media_id],
        storage_keys=[media.storage_key],
        mime_type=media.mime,
    )
    db.commit()
    background_tasks.add_task(_run_agent_bg, auth.business_id, job_id, input_bundle)

    return {
        "job_id": str(job_id),
        "status": "queued",
        "poll_url": f"/v1/jobs/{job_id}",
    }


@router.get(
    "",
    response_model=list[ProductResponse],
    status_code=status.HTTP_200_OK,
    operation_id="listProducts",
    summary="List tenant catalogue products (EP-B04)",
)
async def list_products(
    status_filter: str = "active",
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[ProductResponse]:
    """Retrieve catalog products strictly isolated to tenant."""
    if status_filter not in {"active", "archived", "all"}:
        raise DomainValidationError(detail="status_filter must be active, archived, or all.")
    stmt = select(Product).where(Product.business_id == auth.business_id)
    if status_filter != "all":
        stmt = stmt.where(Product.status == status_filter)
    products = db.execute(stmt.order_by(Product.created_at.desc()).limit(100)).scalars().all()

    result = []
    for p in products:
        var_repo = VariantRepository(session=db, business_id=auth.business_id)
        variant = var_repo.get_first_for_product(p.id)
        result.append(
            ProductResponse(
                id=p.id,
                business_id=p.business_id,
                sku=p.sku,
                name=p.name,
                description=p.description,
                price_inr=p.price_inr,
                field_sources=p.field_sources,
                attributes=p.attributes,
                status=p.status,
                version=p.version,
                stock=variant.stock if variant else 0,
                stock_version=variant.stock_version if variant else 1,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return result


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createProduct",
    summary="Create confirmed product in catalogue (EP-B05)",
)
async def create_product(
    req: ProductCreateRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Create confirmed product manually or from a draft proposal."""
    # If creating from a draft proposal:
    if req.from_draft_proposal_id:
        stmt_prop = select(Proposal).where(
            Proposal.id == req.from_draft_proposal_id,
            Proposal.business_id == auth.business_id,
        )
        proposal = db.execute(stmt_prop).scalar_one_or_none()
        if not proposal:
            raise NotFoundError(f"Proposal {req.from_draft_proposal_id} not found.")

        # Require seller-confirmed price
        if req.price_inr is None or req.price_inr <= 0:
            raise EvidenceMissingError("Creating a product from an AI draft requires a seller-confirmed price.")

    sku = req.sku or f"SKU-{uuid4().hex[:8].upper()}"
    repo = ProductRepository(session=db, business_id=auth.business_id)
    if repo.get_by_sku(sku):
        raise ConflictError(f"Product with SKU '{sku}' already exists.")

    product = Product(
        business_id=auth.business_id,
        sku=sku,
        name=req.name,
        description=req.description,
        price_inr=req.price_inr,
        field_sources={"price_inr": {"source": "confirmed"}},
        attributes={},
        status="active",
        version=1,
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        business_id=auth.business_id,
        product_id=product.id,
        color=req.color,
        size=req.size,
        stock=req.stock,
        stock_version=1,
    )
    db.add(variant)
    db.flush()

    return ProductResponse(
        id=product.id,
        business_id=product.business_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price_inr=product.price_inr,
        field_sources=product.field_sources,
        attributes=product.attributes,
        status=product.status,
        version=product.version,
        stock=variant.stock,
        stock_version=variant.stock_version,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getProduct",
    summary="Get confirmed product detail (EP-B06)",
)
async def get_product(
    product_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Retrieve product detail within tenant scope."""
    repo = ProductRepository(session=db, business_id=auth.business_id)
    product = repo.get_by_id(product_id)
    if not product:
        raise NotFoundError(f"Product {product_id} not found.")

    var_repo = VariantRepository(session=db, business_id=auth.business_id)
    variant = var_repo.get_first_for_product(product_id)

    return ProductResponse(
        id=product.id,
        business_id=product.business_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price_inr=product.price_inr,
        field_sources=product.field_sources,
        attributes=product.attributes,
        status=product.status,
        version=product.version,
        stock=variant.stock if variant else 0,
        stock_version=variant.stock_version if variant else 1,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    operation_id="updateProduct",
    summary="Update product with optimistic concurrency If-Match (EP-B07)",
)
async def update_product(
    product_id: UUID,
    req: ProductPatchRequest,
    if_match: str | None = Header(None, alias="If-Match"),
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ProductResponse:
    """Update product facts enforcing optimistic version locking."""
    repo = ProductRepository(session=db, business_id=auth.business_id)
    product = repo.get_by_id(product_id)
    if not product:
        raise NotFoundError(f"Product {product_id} not found.")

    if if_match is not None:
        clean_match = if_match.strip('"')
        try:
            expected_v = int(clean_match)
            if product.version != expected_v:
                raise StaleVersionError(
                    f"Product has been updated. Expected version {expected_v}, current {product.version}."
                )
        except ValueError:
            raise DomainValidationError(detail="If-Match must contain a numeric product version.") from None

    if not req.model_fields_set.intersection({"name", "description", "price_inr", "attributes"}):
        raise DomainValidationError(detail="At least one product field must be provided.")

    if req.name is not None:
        product.name = req.name
    if "description" in req.model_fields_set:
        product.description = req.description
    if req.price_inr is not None:
        product.price_inr = req.price_inr
    if req.attributes is not None:
        product.attributes = req.attributes

    product.version += 1
    product.updated_at = datetime.now(timezone.utc)
    db.flush()

    var_repo = VariantRepository(session=db, business_id=auth.business_id)
    variant = var_repo.get_first_for_product(product_id)

    return ProductResponse(
        id=product.id,
        business_id=product.business_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price_inr=product.price_inr,
        field_sources=product.field_sources,
        attributes=product.attributes,
        status=product.status,
        version=product.version,
        stock=variant.stock if variant else 0,
        stock_version=variant.stock_version if variant else 1,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.post(
    "/{product_id}/archive",
    status_code=status.HTTP_200_OK,
    operation_id="archiveProduct",
    summary="Soft-delete/archive catalog product (EP-B08)",
)
async def archive_product(
    product_id: UUID,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Archive product if no active open orders exist."""
    repo = ProductRepository(session=db, business_id=auth.business_id)
    success = repo.archive(product_id)
    if not success:
        raise NotFoundError(f"Product {product_id} not found.")
    return {"id": str(product_id), "status": "archived"}


@router.post(
    "/{product_id}/stock",
    status_code=status.HTTP_200_OK,
    operation_id="adjustProductStock",
    summary="Adjust product stock quantity with version check (EP-B09)",
)
async def adjust_product_stock(
    product_id: UUID,
    req: ProductStockAdjustmentRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Atomically adjust variant stock quantity preventing concurrent overwrite and negative stock."""
    repo = ProductRepository(session=db, business_id=auth.business_id)
    product = repo.get_by_id(product_id)
    if not product:
        raise NotFoundError(f"Product {product_id} not found.")

    var_repo = VariantRepository(session=db, business_id=auth.business_id)
    variant = var_repo.get_first_for_product(product_id)
    if not variant:
        raise NotFoundError("Product variant not found.")

    updated_variant = var_repo.adjust_stock(
        variant_id=variant.id,
        delta=req.delta,
        expected_stock_version=req.expected_stock_version,
    )

    return {
        "product_id": str(product_id),
        "stock": updated_variant.stock,
        "stock_version": updated_variant.stock_version,
    }
