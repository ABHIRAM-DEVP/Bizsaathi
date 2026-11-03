"""Owner-only operational metrics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.tenancy import AuthContext, require_owner_or_operator
from app.models.base import get_db
from app.schemas.metrics import AgentMetricsResponse
from app.services.metrics import get_agent_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/agents", response_model=AgentMetricsResponse)
async def read_agent_metrics(
    auth: Annotated[AuthContext, Depends(require_owner_or_operator)],
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=90)] = 30,
) -> AgentMetricsResponse:
    """Return real, tenant-scoped job and graph-node metrics for up to 90 days."""
    return get_agent_metrics(db, business_id=auth.business_id, window_days=days)
