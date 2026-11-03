"""Posts router for social media content generation, claims, and revisions."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppException, NotFoundError, StaleVersionError
from app.core.errors import ValidationError as DomainValidationError
from app.core.logging import logger
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
from app.services.post_generation import create_generated_post, create_quick_generated_post

router = APIRouter(prefix="/posts", tags=["posts"])


def _sse_event(name: str, payload: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload)}\n\n"


def _claim_response(db: Session, claim: Claim) -> ClaimResponse:
    evidence_ids = (
        db.execute(
            select(Evidence.id).where(
                Evidence.business_id == claim.business_id,
                Evidence.claim_id == claim.id,
            )
        )
        .scalars()
        .all()
    )
    return ClaimResponse(
        id=claim.id,
        text=claim.text,
        kind=claim.kind,
        verdict=claim.verdict,
        severity=claim.severity,
        repair_suggestion=claim.repair_suggestion,
        evidence_ids=list(evidence_ids),
    )


@router.post(
    "/generate/{product_id}/quick",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="generateQuickPost",
    summary="Generate an instant local post template",
)
async def generate_quick_post(
    product_id: UUID,
    req: PostGenerateRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> PostResponse:
    """Save a clearly-labelled local template without calling an AI provider."""
    return await create_quick_generated_post(
        db,
        auth=auth,
        product_id=product_id,
        channel=req.channel,
        language=req.language,
    )


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
    request: Request,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> PostResponse:
    """Generate social post copy from confirmed product facts."""
    return await create_generated_post(
        db,
        auth=auth,
        product_id=product_id,
        channel=req.channel,
        language=req.language,
        http_client=getattr(request.app.state, "model_http_client", None),
    )


@router.post(
    "/generate/{product_id}/stream",
    status_code=status.HTTP_200_OK,
    operation_id="streamGeneratePost",
    summary="Stream a generated marketing post draft",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Server-sent events: status, unverified creative-line updates, and the saved post.",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    },
)
async def stream_generate_post(
    product_id: UUID,
    req: PostGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream creative line updates and then the validated, persisted post."""
    updates: asyncio.Queue[tuple[int, str]] = asyncio.Queue()

    def publish_token(line_index: int, text: str) -> None:
        updates.put_nowait((line_index, text))

    async def stream_events():
        task = asyncio.create_task(
            create_generated_post(
                db,
                auth=auth,
                product_id=product_id,
                channel=req.channel,
                language=req.language,
                http_client=getattr(request.app.state, "model_http_client", None),
                on_token=publish_token,
            )
        )
        try:
            yield _sse_event("status", {"message": "Post generation started."})
            while not task.done() or not updates.empty():
                try:
                    line_index, text = await asyncio.wait_for(updates.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse_event("token", {"line_index": line_index, "text": text})

            post = await task
            yield _sse_event("complete", {"post": post.model_dump(mode="json")})
        except AppException as exc:
            yield _sse_event("error", {"detail": exc.detail, "status": exc.status_code})
        except Exception:
            logger.exception(
                "Unexpected error while streaming generated post",
                extra={"request_id": getattr(request.state, "request_id", "req_unknown")},
            )
            yield _sse_event(
                "error",
                {"detail": "Post generation failed unexpectedly.", "status": 500},
            )
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
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
        stmt_c = select(Claim).where(
            Claim.business_id == auth.business_id,
            Claim.post_id == p.id,
            Claim.post_version == p.version,
        )
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
                claims=[_claim_response(db, claim) for claim in claims],
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

    stmt_c = select(Claim).where(
        Claim.business_id == auth.business_id,
        Claim.post_id == post.id,
        Claim.post_version == post.version,
    )
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
        claims=[_claim_response(db, claim) for claim in claims],
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
            raise DomainValidationError(detail="If-Match must contain a numeric post version.") from None

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
        db.execute(
            select(Claim).where(
                Claim.business_id == auth.business_id,
                Claim.post_id == post.id,
                Claim.post_version == post.version,
            )
        )
        .scalars()
        .all()
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
                evidence_ids=[reference.id for reference in refs],
                evidence=refs,
            )
        )
    post.status = "checked"
    overall: Literal["pass", "fail", "needs_owner"]
    if summary["contradicted"]:
        overall = "fail"
    elif not checked or summary["unverified"]:
        overall = "needs_owner"
    else:
        overall = "pass"
    db.flush()
    return ClaimCheckResponse(post_id=post.id, version=post.version, claims=checked, summary=summary, overall=overall)
