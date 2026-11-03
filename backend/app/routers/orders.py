"""Tenant-scoped customer order listing."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.tenancy import AuthContext, require_owner_role
from app.models.base import get_db
from app.schemas.orders import OrderResponse
from app.services.orders import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
OrderStatus = Literal["DRAFT", "AWAITING_PAYMENT", "PAID", "FULFILLED", "CANCELLED", "FAILED"]


@router.get(
    "",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    operation_id="listOrders",
    summary="List tenant customer orders (EP-G01)",
)
async def list_orders(
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    auth: AuthContext = Depends(require_owner_role),
    db: Session = Depends(get_db),
) -> list[OrderResponse]:
    return OrderService(session=db, business_id=auth.business_id).list_orders(
        status_filter=order_status,
        limit=limit,
    )
