"""Idempotently seed clearly synthetic order examples for the local demo tenant."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import InvalidStateError
from app.core.tenancy import DEV_BUSINESS_ID, ensure_development_business
from app.models.domain import (
    Approval,
    CustomerOrder,
    OrderItem,
    OrderStatusHistory,
    Product,
    ProductVariant,
    Proposal,
)

_DEMO_NAMESPACE = UUID("b1ad83f2-5211-4d80-81ec-2ad60c97e32c")
_DEMO_NOTE = "[DEMO SAMPLE] Synthetic trading example. No real customer, payment, or shipment."
_ORDER_EXAMPLES = (
    ("awaiting-approval", "Demo customer: Ananya Rao", "DRAFT", None, None, ("DRAFT",)),
    (
        "awaiting-payment",
        "Demo customer: Neha Kulkarni",
        "AWAITING_PAYMENT",
        None,
        None,
        ("DRAFT", "AWAITING_PAYMENT"),
    ),
    (
        "paid",
        "Demo customer: Ayesha Khan",
        "PAID",
        "upi",
        "DEMO-REFERENCE-PAID",
        ("DRAFT", "AWAITING_PAYMENT", "PAID"),
    ),
    (
        "fulfilled",
        "Demo customer: Kavya Iyer",
        "FULFILLED",
        "cash",
        "DEMO-REFERENCE-FULFILLED",
        ("DRAFT", "AWAITING_PAYMENT", "PAID", "FULFILLED"),
    ),
)


def _stable_id(kind: str, name: str) -> UUID:
    return uuid5(_DEMO_NAMESPACE, f"{kind}:{name}")


def seed_demo_orders(session: Session) -> dict[str, int]:
    """Create sample orders and one actionable owner approval for the local demo business."""
    if settings.ENV != "dev":
        raise InvalidStateError("Demo order data can only be seeded when ENV=dev.")

    ensure_development_business(session)
    catalog_row = session.execute(
        select(Product, ProductVariant)
        .join(
            ProductVariant,
            (ProductVariant.product_id == Product.id)
            & (ProductVariant.business_id == DEV_BUSINESS_ID),
        )
        .where(Product.business_id == DEV_BUSINESS_ID, Product.status == "active")
        .order_by(Product.created_at.asc())
        .limit(1)
    ).first()
    if catalog_row is None:
        raise InvalidStateError("Add an active catalog product with a variant before seeding demo orders.")
    product, variant = catalog_row
    price = Decimal(product.price_inr)
    now = datetime.now(timezone.utc)
    orders_by_key: dict[str, CustomerOrder] = {}
    created_orders = 0

    for index, (key, customer_name, order_status, payment_method, payment_reference, history_states) in enumerate(
        _ORDER_EXAMPLES
    ):
        idempotency_key = f"demo-seed:orders:v1:{key}"
        order = session.execute(
            select(CustomerOrder).where(
                CustomerOrder.business_id == DEV_BUSINESS_ID,
                CustomerOrder.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if order is None:
            order_id = _stable_id("order", key)
            created_at = now - timedelta(hours=index * 8 + 1)
            order = CustomerOrder(
                id=order_id,
                business_id=DEV_BUSINESS_ID,
                status=order_status,
                customer_name=customer_name,
                delivery_note=_DEMO_NOTE,
                total_inr=price,
                payment_method=payment_method,
                payment_reference=payment_reference,
                idempotency_key=idempotency_key,
                version=1,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(order)
            session.flush()
            session.add(
                OrderItem(
                    id=_stable_id("order-item", key),
                    business_id=DEV_BUSINESS_ID,
                    order_id=order.id,
                    variant_id=variant.id,
                    qty=1,
                    unit_price_inr=price,
                )
            )

            previous_status: str | None = None
            for history_index, history_status in enumerate(history_states):
                session.add(
                    OrderStatusHistory(
                        business_id=DEV_BUSINESS_ID,
                        order_id=order.id,
                        from_status=previous_status,
                        to_status=history_status,
                        actor_type="system",
                        actor_id="demo-seed",
                        detail={"demo_sample": True, "note": _DEMO_NOTE},
                        at=created_at + timedelta(minutes=history_index * 10),
                    )
                )
                previous_status = history_status
            created_orders += 1
        orders_by_key[key] = order

    pending_order = orders_by_key["awaiting-approval"]
    approval_id = _stable_id("approval", "awaiting-approval")
    existing_approval = session.execute(select(Approval).where(Approval.id == approval_id)).scalar_one_or_none()
    created_approvals = 0
    if existing_approval is None:
        proposal_id = _stable_id("proposal", "awaiting-approval")
        session.add(
            Proposal(
                id=proposal_id,
                business_id=DEV_BUSINESS_ID,
                root_id=proposal_id,
                type="order_action",
                version=1,
                payload={
                    "fields": {"order_id": str(pending_order.id), "action": "approve_order"},
                    "seller_confirmed_fields": [],
                    "demo_sample": True,
                },
                status="pending",
            )
        )
        session.flush()
        session.add(
            Approval(
                id=approval_id,
                business_id=DEV_BUSINESS_ID,
                proposal_id=proposal_id,
                type="order_action",
                status="pending",
                warnings=["Synthetic demo order; not a real customer request."],
                risk="low",
                side_effect={
                    "action": "approve_order",
                    "order_id": str(pending_order.id),
                    "description": "Approve the synthetic demo order and move it to awaiting payment.",
                },
                expires_at=now + timedelta(days=30),
            )
        )
        created_approvals = 1

    session.flush()
    return {"orders_created": created_orders, "approvals_created": created_approvals}
