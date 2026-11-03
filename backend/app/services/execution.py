"""Execution Service: The SOLE authorized writer of confirmed product facts from proposals.

ARCHITECTURAL BOUNDARY:
- Agents propose; deterministic code validates; the seller approves; the execution service writes.
- This module MUST NOT be imported by any module in app.agents (tested by test_module_boundaries.py).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import (
    ConflictError,
    EvidenceMissingError,
    InvalidStateError,
    NotFoundError,
)
from app.models.domain import (
    Approval,
    AuditEvent,
    CustomerOrder,
    Execution,
    OrderStatusHistory,
    Product,
    ProductVariant,
    Proposal,
)


class ExecutionService:
    """Applies approved proposal side-effects to create or update confirmed catalog facts."""

    def __init__(self, session: Session, business_id: UUID):
        self._session = session
        self._business_id = business_id

    def execute_approval(
        self,
        approval_id: UUID,
        idempotency_key: str,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute an approved proposal, creating confirmed catalog entries."""
        # 1. Check idempotency: if execution already exists, return existing receipt
        stmt_exec = select(Execution).where(
            Execution.business_id == self._business_id,
            Execution.idempotency_key == idempotency_key,
        )
        existing_exec = self._session.execute(stmt_exec).scalar_one_or_none()
        if existing_exec:
            return {
                "execution_id": str(existing_exec.id),
                "status": existing_exec.status,
                "result_ref": existing_exec.result_ref,
                "is_cached": True,
            }

        # Also check if this exact approval was already executed under another key
        stmt_app_exec = select(Execution).where(
            Execution.approval_id == approval_id,
        )
        if self._session.execute(stmt_app_exec).scalar_one_or_none():
            raise ConflictError("This approval has already been executed.")

        # 2. Fetch approval and ensure it belongs to this business and is approved
        stmt_app = select(Approval).where(
            Approval.id == approval_id,
            Approval.business_id == self._business_id,
        )
        approval = self._session.execute(stmt_app).scalar_one_or_none()
        if not approval:
            raise NotFoundError(f"Approval {approval_id} not found.")

        if approval.status != "approved":
            raise InvalidStateError(f"Approval status is '{approval.status}', expected 'approved'.")

        now = datetime.now(timezone.utc)
        if approval.expires_at < now:
            raise InvalidStateError("Approval has expired.")

        # 3. Fetch proposal
        stmt_prop = select(Proposal).where(
            Proposal.id == approval.proposal_id,
            Proposal.business_id == self._business_id,
        )
        proposal = self._session.execute(stmt_prop).scalar_one_or_none()
        if not proposal:
            raise NotFoundError(f"Proposal {approval.proposal_id} not found.")

        payload = proposal.payload
        if approval.type == "order_action":
            result_ref = self._approve_order_action(approval, payload, actor_id)
            proposal.status = "executed"
            execution = Execution(
                id=uuid4(),
                business_id=self._business_id,
                approval_id=approval_id,
                idempotency_key=idempotency_key,
                status="succeeded",
                result_ref=result_ref,
            )
            self._session.add(execution)
            self._session.flush()
            return {
                "execution_id": str(execution.id),
                "status": "succeeded",
                "result_ref": result_ref,
                "is_cached": False,
            }

        seller_confirmed = payload.get("seller_confirmed_fields", [])

        # STRICT VALIDATION: price_inr and stock MUST be confirmed by seller
        if "price_inr" not in seller_confirmed or "stock" not in seller_confirmed:
            raise EvidenceMissingError(
                "Missing seller confirmation: 'price_inr' and 'stock' must be in seller_confirmed_fields."
            )

        fields = payload.get("fields", {})
        price_val = Decimal(str(fields.get("price_inr", 0)))
        if price_val < 0:
            raise InvalidStateError("Price cannot be negative.")

        stock_val = int(fields.get("stock", 0))
        if stock_val < 0:
            raise InvalidStateError("Stock cannot be negative.")

        # 4. Perform the write
        if approval.type == "product_create":
            product_id = uuid4()
            sku = fields.get("sku") or f"SKU-{uuid4().hex[:8].upper()}"
            name = fields.get("name", "New Product")

            product = Product(
                id=product_id,
                business_id=self._business_id,
                sku=sku,
                name=name,
                description=fields.get("description"),
                price_inr=price_val,
                field_sources=payload.get("field_sources", {}),
                attributes=fields.get("attributes", {}),
                status="active",
                version=1,
            )
            self._session.add(product)

            # Create default variant with confirmed stock
            variant = ProductVariant(
                business_id=self._business_id,
                product_id=product_id,
                color=fields.get("color"),
                size=fields.get("size"),
                stock=stock_val,
                stock_version=1,
            )
            self._session.add(variant)

            # Record audit event
            audit = AuditEvent(
                business_id=self._business_id,
                actor_type="user" if actor_id else "system",
                actor_id=actor_id,
                action="product.created",
                entity_type="product",
                entity_id=str(product_id),
                detail={"sku": sku, "price_inr": str(price_val), "stock": stock_val},
            )
            self._session.add(audit)
            result_ref = {"product_id": str(product_id), "sku": sku}

        elif approval.type == "product_update":
            product_id_str = fields.get("product_id")
            if not product_id_str:
                raise InvalidStateError("Missing product_id for product_update")
            p_uuid = UUID(product_id_str)

            stmt_p = select(Product).where(
                Product.id == p_uuid,
                Product.business_id == self._business_id,
            )
            existing_product = self._session.execute(stmt_p).scalar_one_or_none()
            if not existing_product:
                raise NotFoundError("Product to update not found.")

            old_price = str(existing_product.price_inr)
            existing_product.price_inr = price_val
            if "name" in fields:
                existing_product.name = fields["name"]
            existing_product.version += 1

            audit = AuditEvent(
                business_id=self._business_id,
                actor_type="user" if actor_id else "system",
                actor_id=actor_id,
                action="product.price_changed",
                entity_type="product",
                entity_id=str(p_uuid),
                detail={"before": old_price, "after": str(price_val)},
            )
            self._session.add(audit)
            result_ref = {"product_id": str(p_uuid), "price_inr": str(price_val)}
        else:
            raise InvalidStateError(f"Unsupported approval execution type: {approval.type}")

        # Mark proposal as executed
        proposal.status = "executed"

        # 5. Record execution receipt
        exec_id = uuid4()
        execution = Execution(
            id=exec_id,
            business_id=self._business_id,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
            status="succeeded",
            result_ref=result_ref,
        )
        self._session.add(execution)
        self._session.flush()

        return {
            "execution_id": str(exec_id),
            "status": "succeeded",
            "result_ref": result_ref,
            "is_cached": False,
        }

    def _approve_order_action(
        self,
        approval: Approval,
        payload: dict[str, Any],
        actor_id: str | None,
    ) -> dict[str, str]:
        fields = payload.get("fields")
        if not isinstance(fields, dict):
            raise InvalidStateError("Order approval is missing its action fields.")
        if fields.get("action") != "approve_order" or approval.side_effect.get("action") != "approve_order":
            raise InvalidStateError("Unsupported order approval action.")

        order_id_value = fields.get("order_id")
        if not isinstance(order_id_value, str) or approval.side_effect.get("order_id") != order_id_value:
            raise InvalidStateError("Order approval does not identify a matching order.")
        try:
            order_id = UUID(order_id_value)
        except ValueError as exc:
            raise InvalidStateError("Order approval contains an invalid order ID.") from exc

        order = self._session.execute(
            select(CustomerOrder)
            .where(
                CustomerOrder.id == order_id,
                CustomerOrder.business_id == self._business_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status != "DRAFT":
            raise InvalidStateError(f"Only DRAFT orders can be approved; current status is '{order.status}'.")

        order.status = "AWAITING_PAYMENT"
        order.version += 1
        self._session.add(
            OrderStatusHistory(
                business_id=self._business_id,
                order_id=order.id,
                from_status="DRAFT",
                to_status="AWAITING_PAYMENT",
                actor_type="user" if actor_id else "system",
                actor_id=actor_id,
                detail={"approval_id": str(approval.id), "action": "approve_order"},
            )
        )
        self._session.add(
            AuditEvent(
                business_id=self._business_id,
                actor_type="user" if actor_id else "system",
                actor_id=actor_id,
                action="order.approved",
                entity_type="customer_order",
                entity_id=str(order.id),
                detail={"approval_id": str(approval.id), "status": "AWAITING_PAYMENT"},
            )
        )
        return {"order_id": str(order.id), "status": order.status}
