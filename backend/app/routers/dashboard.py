"""Dashboard router (EP-I01)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Return tenant-scoped approval, escalation, stock, and job data."""
    return get_dashboard_summary(db, business_id=auth.business_id)
