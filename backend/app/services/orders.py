"""Tenant-scoped customer order read operations."""

from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import CustomerOrder, OrderItem, Product, ProductVariant
from app.schemas.orders import OrderItemResponse, OrderResponse

OrderStatus = Literal["DRAFT", "AWAITING_PAYMENT", "PAID", "FULFILLED", "CANCELLED", "FAILED"]


class OrderService:
    def __init__(self, session: Session, business_id: UUID):
        self._session = session
        self._business_id = business_id

    def list_orders(self, status_filter: OrderStatus | None, limit: int) -> list[OrderResponse]:
        statement = select(CustomerOrder).where(CustomerOrder.business_id == self._business_id)
        if status_filter is not None:
            statement = statement.where(CustomerOrder.status == status_filter)
        orders = self._session.execute(
            statement.order_by(CustomerOrder.created_at.desc()).limit(limit)
        ).scalars().all()
        if not orders:
            return []

        order_ids: list[UUID] = [order.id for order in orders]
        item_rows = self._session.execute(
            select(OrderItem, Product)
            .join(
                ProductVariant,
                (ProductVariant.id == OrderItem.variant_id)
                & (ProductVariant.business_id == self._business_id),
            )
            .join(
                Product,
                (Product.id == ProductVariant.product_id) & (Product.business_id == self._business_id),
            )
            .where(
                OrderItem.business_id == self._business_id,
                OrderItem.order_id.in_(order_ids),
            )
        ).all()

        items_by_order: dict[UUID, list[OrderItemResponse]] = {order_id: [] for order_id in order_ids}
        for item, product in item_rows:
            items_by_order[item.order_id].append(
                OrderItemResponse(
                    variant_id=item.variant_id,
                    product_name=product.name,
                    quantity=item.qty,
                    unit_price_inr=item.unit_price_inr,
                )
            )

        return [
            OrderResponse(
                id=order.id,
                status=order.status,
                customer_name=order.customer_name,
                total_inr=order.total_inr,
                payment_method=order.payment_method,
                delivery_note=order.delivery_note,
                demo_sample=bool(order.delivery_note and order.delivery_note.startswith("[DEMO SAMPLE]")),
                created_at=order.created_at,
                items=items_by_order[order.id],
            )
            for order in orders
        ]
