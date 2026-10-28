"""Approvals router implementing human-in-the-loop review and version-bound decision gates."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import (
    NotFoundError,
    StaleVersionError,
)
from app.core.tenancy import AuthContext, require_owner_role, require_tenant
from app.models.base import get_db
from app.models.domain import Approval, Proposal
from app.schemas.approvals import (
    ApprovalDecisionRequest,
    ApprovalEditRequest,
    ApprovalResponse,
)
from app.services.execution import ExecutionService

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get(
    "",
    response_model=list[ApprovalResponse],
    status_code=status.HTTP_200_OK,
    operation_id="listApprovals",
    summary="List pending approvals (EP-D01)",
)
async def list_approvals(
    status_filter: str = "pending",
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> list[ApprovalResponse]:
    """Retrieve all approvals within tenant scope."""
    stmt = (
        select(Approval)
        .where(
            Approval.business_id == auth.business_id,
            Approval.status == status_filter,
        )
        .order_by(Approval.created_at.desc())
    )
    approvals = db.execute(stmt).scalars().all()

    result = []
    for a in approvals:
        stmt_p = select(Proposal).where(Proposal.id == a.proposal_id)
        prop = db.execute(stmt_p).scalar_one_or_none()
        prop_ver = prop.version if prop else 1
        result.append(
            ApprovalResponse(
                id=a.id,
                business_id=a.business_id,
                proposal_id=a.proposal_id,
                type=a.type,
                status=a.status,
                warnings=a.warnings,
                risk=a.risk,
                side_effect=a.side_effect,
                proposal_version=prop_ver,
                diff={},
                expires_at=a.expires_at,
                decided_by=a.decided_by,
                decided_at=a.decided_at,
                decision_reason=a.decision_reason,
                created_at=a.created_at,
            )
        )
    return result


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    status_code=status.HTTP_200_OK,
    operation_id="getApproval",
    summary="Get approval request detail with proposal diff and warnings (EP-D02)",
)
async def get_approval(
    approval_id: UUID,
    auth: AuthContext = Depends(require_tenant),
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    """Retrieve detailed approval item with proposal payload diff."""
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.business_id == auth.business_id,
    )
    approval = db.execute(stmt).scalar_one_or_none()
    if not approval:
        raise NotFoundError(f"Approval {approval_id} not found.")

    stmt_p = select(Proposal).where(Proposal.id == approval.proposal_id)
    proposal = db.execute(stmt_p).scalar_one_or_none()
    prop_ver = proposal.version if proposal else 1
    diff = proposal.payload if proposal else {}

    return ApprovalResponse(
        id=approval.id,
        business_id=approval.business_id,
        proposal_id=approval.proposal_id,
        type=approval.type,
        status=approval.status,
        warnings=approval.warnings,
        risk=approval.risk,
        side_effect=approval.side_effect,
        proposal_version=prop_ver,
        diff=diff,
        expires_at=approval.expires_at,
        decided_by=approval.decided_by,
        decided_at=approval.decided_at,
        decision_reason=approval.decision_reason,
        created_at=approval.created_at,
    )


@router.post(
    "/{approval_id}/approve",
    status_code=status.HTTP_200_OK,
    operation_id="approveProposal",
    summary="Approve proposal bound to exact proposal version and trigger execution (EP-D03)",
)
async def approve_proposal(
    approval_id: UUID,
    req: ApprovalDecisionRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve a proposal version and trigger deterministic execution."""
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.business_id == auth.business_id,
    )
    approval = db.execute(stmt).scalar_one_or_none()
    if not approval:
        raise NotFoundError(f"Approval {approval_id} not found.")

    stmt_p = select(Proposal).where(Proposal.id == approval.proposal_id)
    proposal = db.execute(stmt_p).scalar_one_or_none()
    if not proposal:
        raise NotFoundError("Referenced proposal not found.")

    # Guard: Version binding
    if proposal.version != req.expected_proposal_version:
        raise StaleVersionError(
            f"Stale approval decision: Proposal has version {proposal.version}, "
            f"but decision bound to version {req.expected_proposal_version}."
        )

    now = datetime.now(timezone.utc)
    approval.status = "approved"
    approval.decided_at = now
    approval.decided_by = auth.user_id
    approval.decision_reason = req.decision_reason
    proposal.status = "approved"
    db.flush()

    # Call execution service
    exec_key = idempotency_key or f"idem_{approval_id.hex}"
    exec_service = ExecutionService(session=db, business_id=auth.business_id)
    receipt = exec_service.execute_approval(
        approval_id=approval_id,
        idempotency_key=exec_key,
        actor_id=str(auth.user_id),
    )

    return {
        "approval_id": str(approval_id),
        "status": "approved",
        "execution": receipt,
    }


@router.post(
    "/{approval_id}/reject",
    status_code=status.HTTP_200_OK,
    operation_id="rejectProposal",
    summary="Reject proposal (EP-D04)",
)
async def reject_proposal(
    approval_id: UUID,
    req: ApprovalDecisionRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reject proposal and close approval review."""
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.business_id == auth.business_id,
    )
    approval = db.execute(stmt).scalar_one_or_none()
    if not approval:
        raise NotFoundError(f"Approval {approval_id} not found.")

    stmt_p = select(Proposal).where(Proposal.id == approval.proposal_id)
    proposal = db.execute(stmt_p).scalar_one_or_none()

    approval.status = "rejected"
    approval.decided_at = datetime.now(timezone.utc)
    approval.decided_by = auth.user_id
    approval.decision_reason = req.decision_reason
    if proposal:
        proposal.status = "rejected"
    db.flush()

    return {"approval_id": str(approval_id), "status": "rejected"}


@router.post(
    "/{approval_id}/edit",
    status_code=status.HTTP_200_OK,
    operation_id="editProposal",
    summary="Edit proposal fields, invalidating current approval and issuing next version (EP-D05)",
)
async def edit_proposal(
    approval_id: UUID,
    req: ApprovalEditRequest,
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Edit proposal fields. Invalidates old approval and generates incremented proposal version."""
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.business_id == auth.business_id,
    )
    approval = db.execute(stmt).scalar_one_or_none()
    if not approval:
        raise NotFoundError(f"Approval {approval_id} not found.")

    stmt_p = select(Proposal).where(Proposal.id == approval.proposal_id)
    old_proposal = db.execute(stmt_p).scalar_one_or_none()
    if not old_proposal:
        raise NotFoundError("Proposal not found.")

    # Invalidate previous approval and proposal version
    approval.status = "invalidated"
    old_proposal.status = "invalidated"

    # Merge fields
    merged_fields = {**old_proposal.payload.get("fields", {}), **req.updated_fields}
    new_payload = {
        **old_proposal.payload,
        "fields": merged_fields,
        "seller_confirmed_fields": req.seller_confirmed_fields,
    }

    # Create new proposal version
    new_prop_id = uuid4()
    new_version = old_proposal.version + 1
    new_proposal = Proposal(
        id=new_prop_id,
        business_id=auth.business_id,
        root_id=old_proposal.root_id,
        job_id=old_proposal.job_id,
        type=old_proposal.type,
        version=new_version,
        payload=new_payload,
        status="pending",
    )
    db.add(new_proposal)

    # Issue new approval tied to new proposal version
    from datetime import timedelta

    new_app_id = uuid4()
    new_approval = Approval(
        id=new_app_id,
        business_id=auth.business_id,
        proposal_id=new_prop_id,
        type=approval.type,
        status="pending",
        warnings=[],
        risk="low",
        side_effect=approval.side_effect,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(new_approval)
    db.flush()

    return {
        "old_approval_id": str(approval_id),
        "new_approval_id": str(new_app_id),
        "new_proposal_id": str(new_prop_id),
        "new_version": new_version,
    }
