"""
Dashboard router (EP-I01).
Returns aggregated metrics and next-step guidance.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db)
) -> DashboardResponse:
    """
    Dashboard summary (EP-I01).
    Returns: pending approvals count, open escalations, low stock items, recent jobs.
    """
    business_id = auth.business_id
    
    # TODO: Query actual data from database
    # For now, return mock structure that frontend expects
    return DashboardResponse(
        pending_approvals=3,  # Mock data
        open_escalations=0,
        recent_jobs=[],
        low_stock=[],
        next_step=None
    )
