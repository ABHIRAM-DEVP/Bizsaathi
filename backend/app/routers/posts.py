"""Posts router for social media content generation, claims, and revisions."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, StaleVersionError
from app.core.tenancy import AuthContext, require_owner_role, require_tenant
from app.models.base import get_db
from app.models.domain import Claim, Evidence, Post, PostRevision, Product
from app.schemas.posts import (
    ClaimCheckItemResponse,
    ClaimCheckRequest,
    ClaimCheckResponse,
    ClaimResponse,
    EvidenceReference,
    PostGenerateRequest,
    PostPatchRequest,
    PostResponse,
)
from app.services.claim_verifier import verify_claim

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "/generate/{product_id}",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="generatePost",
    summary="Generate marketing post draft with claims (EP-C01)",
)
async def generate_post(
    product_id: UUID,
    req: PostGenerateRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> PostResponse:
    """Generate social post copy from confirmed product facts."""
    # Verify product is active and has confirmed name and price
    stmt_p = select(Product).where(
        Product.id == product_id,
        Product.business_id == auth.business_id,
    )
    product = db.execute(stmt_p).scalar_one_or_none()
    if not product:
        raise NotFoundError(f"Product {product_id} not found.")

    if product.status != "active":
        raise ConflictError("Product must be active to generate posts.")

    if product.price_inr is None or product.price_inr <= 0:
        raise ConflictError("Product missing confirmed price.")

    # Generate draft text with deterministic price
    price_f = float(product.price_inr)
    text = (
        f"Elevate your wardrobe with our {product.name}! Handcrafted excellence designed for comfort. "
        f"Get yours today for only ₹{price_f:.2f}."
    )

    post_id = uuid4()
    provenance = {
        "model_id": "mock-model-v1",
        "prompt_version": 1,
        "mode": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    post = Post(
        id=post_id,
        business_id=auth.business_id,
        product_id=product_id,
        channel=req.channel,
        language=req.language,
        text=text,
        version=1,
        status="draft",
        provenance=provenance,
    )
    db.add(post)

    # Add initial revision
    rev = PostRevision(
        post_id=post_id,
        business_id=auth.business_id,
        version=1,
        text=text,
    )
    db.add(rev)

    # Add claims
    claim1 = Claim(
        business_id=auth.business_id,
        post_id=post_id,
        post_version=1,
        text=f"Product price is ₹{price_f:.2f}",
        kind="fact",
        verdict="supported",
    )
    claim2 = Claim(
        business_id=auth.business_id,
        post_id=post_id,
        post_version=1,
        text=f"Product name is {product.name}",
        kind="fact",
        verdict="supported",
    )
    db.add_all([claim1, claim2])
    db.flush()

    return PostResponse(
        id=post.id,
        business_id=post.business_id,
        product_id=post.product_id,
        channel=post.channel,
        language=post.language,
        text=post.text,
        version=post.version,
        status=post.status,
        provenance=post.provenance,
        claims=[
            ClaimResponse(id=claim1.id, text=claim1.text, kind=claim1.kind, verdict=claim1.verdict),
            ClaimResponse(id=claim2.id, text=claim2.text, kind=claim2.kind, verdict=claim2.verdict),
        ],
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get(
    "",
    response_model=list[PostResponse],
    status_code=status.HTTP_200_OK,
    operation_id="listPosts",
    summary="List generated posts (EP-C02)",
)
async def list_posts(
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    """List tenant post drafts."""
    stmt = select(Post).where(Post.business_id == auth.business_id).order_by(Post.created_at.desc())
    posts = db.execute(stmt).scalars().all()

    result = []
    for p in posts:
        stmt_c = select(Claim).where(Claim.post_id == p.id, Claim.post_version == p.version)
        claims = db.execute(stmt_c).scalars().all()
        result.append(
            PostResponse(
                id=p.id,
                business_id=p.business_id,
                product_id=p.product_id,
                channel=p.channel,
                language=p.language,
                text=p.text,
                version=p.version,
                status=p.status,
                provenance=p.provenance,
                claims=[ClaimResponse(id=c.id, text=c.text, kind=c.kind, verdict=c.verdict) for c in claims],
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return result


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getPost",
    summary="Get post draft detail and claim list (EP-C03)",
)
async def get_post(
    post_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> PostResponse:
    """Retrieve post detail within tenant scope."""
    stmt = select(Post).where(
        Post.id == post_id,
        Post.business_id == auth.business_id,
    )
    post = db.execute(stmt).scalar_one_or_none()
    if not post:
        raise NotFoundError(f"Post {post_id} not found.")

    stmt_c = select(Claim).where(Claim.post_id == post.id, Claim.post_version == post.version)
    claims = db.execute(stmt_c).scalars().all()

    return PostResponse(
        id=post.id,
        business_id=post.business_id,
        product_id=post.product_id,
        channel=post.channel,
        language=post.language,
        text=post.text,
        version=post.version,
        status=post.status,
        provenance=post.provenance,
        claims=[ClaimResponse(id=c.id, text=c.text, kind=c.kind, verdict=c.verdict) for c in claims],
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
    operation_id="updatePost",
    summary="Update post draft creating a new revision and invalidating prior claims (EP-C04)",
)
async def update_post(
    post_id: UUID,
    req: PostPatchRequest,
    if_match: str | None = Header(None, alias="If-Match"),
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> PostResponse:
    """Update post text. Increments version and creates new revision row."""
    stmt = select(Post).where(
        Post.id == post_id,
        Post.business_id == auth.business_id,
    )
    post = db.execute(stmt).scalar_one_or_none()
    if not post:
        raise NotFoundError(f"Post {post_id} not found.")

    if if_match is not None:
        clean_match = if_match.strip('"')
        try:
            expected_v = int(clean_match)
            if post.version != expected_v:
                raise StaleVersionError(
                    f"Post has been modified. Expected version {expected_v}, current {post.version}."
                )
        except ValueError:
            pass

    new_version = post.version + 1
    post.version = new_version
    post.text = req.text
    post.status = "draft"  # Return status to draft upon edit
    post.updated_at = datetime.now(timezone.utc)

    # Add new revision row
    rev = PostRevision(
        post_id=post.id,
        business_id=auth.business_id,
        version=new_version,
        text=req.text,
    )
    db.add(rev)
    db.flush()

    return PostResponse(
        id=post.id,
        business_id=post.business_id,
        product_id=post.product_id,
        channel=post.channel,
        language=post.language,
        text=post.text,
        version=post.version,
        status=post.status,
        provenance=post.provenance,
        claims=[],  # Prior claims are invalidated for new version
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.post(
    "/{post_id}/claim-check",
    response_model=ClaimCheckResponse,
    status_code=status.HTTP_200_OK,
    operation_id="checkPostClaims",
    summary="Verify current post claims against confirmed evidence (EP-C05)",
)
async def check_post_claims(
    post_id: UUID,
    req: ClaimCheckRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> ClaimCheckResponse:
    stmt = select(Post).where(Post.id == post_id, Post.business_id == auth.business_id)
    post = db.execute(stmt).scalar_one_or_none()
    if not post:
        raise NotFoundError(f"Post {post_id} not found.")
    if post.version != req.version:
        raise StaleVersionError(f"Post version {post.version} is current; request used {req.version}.")
    product = db.execute(
        select(Product).where(Product.id == post.product_id, Product.business_id == auth.business_id)
    ).scalar_one_or_none()
    if not product:
        raise NotFoundError("Confirmed product for post not found.")

    claims = (
        db.execute(select(Claim).where(Claim.post_id == post.id, Claim.post_version == post.version)).scalars().all()
    )
    checked: list[ClaimCheckItemResponse] = []
    summary = {"supported": 0, "contradicted": 0, "unverified": 0}
    for claim in claims:
        verdict, severity, snapshot, repair = verify_claim(claim, product)
        claim.verdict, claim.severity, claim.repair_suggestion = verdict, severity, repair
        refs: list[EvidenceReference] = []
        if snapshot is not None:
            evidence = Evidence(
                business_id=auth.business_id,
                claim_id=claim.id,
                source_kind="product",
                source_id=product.id,
                source_version=product.version,
                snapshot=snapshot,
            )
            db.add(evidence)
            db.flush()
            refs.append(
                EvidenceReference(
                    id=evidence.id,
                    source_kind="product",
                    source_id=product.id,
                    source_version=product.version,
                )
            )
        summary[verdict] += 1
        checked.append(
            ClaimCheckItemResponse(
                id=claim.id,
                text=claim.text,
                kind=claim.kind,
                verdict=verdict,
                severity=severity,
                repair_suggestion=repair,
                evidence=refs,
            )
        )
    post.status = "checked"
    overall: Literal["pass", "fail", "needs_owner"]
    if summary["contradicted"]:
        overall = "fail"
    elif summary["unverified"]:
        overall = "needs_owner"
    else:
        overall = "pass"
    db.flush()
    return ClaimCheckResponse(post_id=post.id, version=post.version, claims=checked, summary=summary, overall=overall)
