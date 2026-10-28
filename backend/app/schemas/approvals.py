"""Pydantic schemas for approvals core endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalDecisionRequest(BaseModel):
    """Seller decision request bound to expected proposal version."""

    expected_proposal_version: int = Field(ge=1, description="Proposal version approved (prevents stale approvals)")
    decision_reason: str | None = Field(default=None, max_length=500)


class ApprovalEditRequest(BaseModel):
    """Proposal edit request which invalidates the current approval and issues a new version."""

    updated_fields: dict[str, Any] = Field(description="Seller-modified proposal fields")
    seller_confirmed_fields: list[str] = Field(
        default=["price_inr", "stock"],
        description="Fields explicitly verified by the seller",
    )


class ApprovalResponse(BaseModel):
    """Approval request bound to an exact proposal version."""

    id: UUID
    business_id: UUID
    proposal_id: UUID
    type: str
    status: str
    warnings: list[Any]
    risk: str
    side_effect: dict[str, Any]
    proposal_version: int = 1
    diff: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = None
    created_at: datetime
