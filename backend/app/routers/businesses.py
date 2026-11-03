"""Owner business profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.models.domain import Business
from app.schemas.businesses import BusinessProfileResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/me", response_model=BusinessProfileResponse, summary="Get the current owner's public store identity")
def get_current_business(
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> BusinessProfileResponse:
    business = db.execute(select(Business).where(Business.id == auth.business_id)).scalar_one_or_none()
    if business is None:
        raise NotFoundError(f"Business {auth.business_id} not found.")
    return BusinessProfileResponse(id=business.id, name=business.name, slug=business.slug)
