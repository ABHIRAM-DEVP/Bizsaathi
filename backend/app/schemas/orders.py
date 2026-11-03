"""Response schemas for tenant-scoped customer orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    variant_id: UUID
    product_name: str
    quantity: int
    unit_price_inr: Decimal


class OrderResponse(BaseModel):
    id: UUID
    status: str
    customer_name: str
    total_inr: Decimal
    payment_method: str | None
    delivery_note: str | None
    demo_sample: bool
    created_at: datetime
    items: list[OrderItemResponse]
