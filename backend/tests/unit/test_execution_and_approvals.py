"""Unit tests for Products, Stock, and Approval Execution Core (T-203)."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.errors import (
    EvidenceMissingError,
    InvalidStateError,
    StaleVersionError,
)
from app.models.domain import Approval, ProductVariant, Proposal
from app.repositories.variant import VariantRepository
from app.services.execution import ExecutionService


class MemoryDbSession:
    """In-memory mock session supporting simple entity maps."""

    def __init__(self, entities=None):
        self.entities = {e.id: e for e in (entities or []) if hasattr(e, "id")}
        self.added = []

    def add(self, obj):
        if hasattr(obj, "id") and obj.id:
            self.entities[obj.id] = obj
        self.added.append(obj)

    def flush(self):
        pass

    def execute(self, stmt):
        class ScalarResult:
            def __init__(self, items):
                self._items = items

            def scalar_one_or_none(self):
                return self._items[0] if self._items else None

            def scalars(self):
                return self

            def all(self):
                return self._items

        compiled = stmt.compile()
        params = compiled.params
        param_vals = list(params.values())

        matching = []
        for e in list(self.entities.values()) + self.added:
            if hasattr(e, "business_id") and e.business_id in param_vals:
                if hasattr(e, "id") and e.id in param_vals:
                    matching.append(e)
                elif hasattr(e, "approval_id") and e.approval_id in param_vals:
                    matching.append(e)
                elif hasattr(e, "idempotency_key") and e.idempotency_key in param_vals:
                    matching.append(e)
                elif hasattr(e, "proposal_id") and e.proposal_id in param_vals:
                    matching.append(e)
                elif hasattr(e, "status") and e.status in param_vals:
                    matching.append(e)
                elif hasattr(e, "product_id") and e.product_id in param_vals:
                    matching.append(e)
                elif hasattr(e, "sku") and e.sku in param_vals:
                    matching.append(e)
        return ScalarResult(matching)


def test_draft_missing_seller_confirmed_price_fails():
    b_id = uuid4()
    prop_id = uuid4()
    app_id = uuid4()

    proposal = Proposal(
        id=prop_id,
        business_id=b_id,
        root_id=prop_id,
        type="product_create",
        version=1,
        payload={
            "fields": {"name": "Shirt", "price_inr": 499.00},
            "seller_confirmed_fields": [],  # Price NOT confirmed
        },
        status="pending",
    )
    approval = Approval(
        id=app_id,
        business_id=b_id,
        proposal_id=prop_id,
        type="product_create",
        status="approved",
        side_effect={"description": "Create product"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db = MemoryDbSession([proposal, approval])

    exec_service = ExecutionService(session=db, business_id=b_id)
    with pytest.raises(EvidenceMissingError) as exc_info:
        exec_service.execute_approval(app_id, idempotency_key="idem-key-1")
    assert "Missing seller confirmation" in str(exc_info.value)


def test_idempotent_approval_execution():
    b_id = uuid4()
    prop_id = uuid4()
    app_id = uuid4()

    proposal = Proposal(
        id=prop_id,
        business_id=b_id,
        root_id=prop_id,
        type="product_create",
        version=1,
        payload={
            "fields": {"name": "Shirt", "sku": "SHIRT-1", "price_inr": 499.00, "stock": 10},
            "seller_confirmed_fields": ["price_inr", "stock"],
        },
        status="pending",
    )
    approval = Approval(
        id=app_id,
        business_id=b_id,
        proposal_id=prop_id,
        type="product_create",
        status="approved",
        side_effect={"description": "Create product"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db = MemoryDbSession([proposal, approval])

    exec_service = ExecutionService(session=db, business_id=b_id)

    # First call
    receipt1 = exec_service.execute_approval(app_id, idempotency_key="idem-key-repeat")
    assert receipt1["status"] == "succeeded"
    assert receipt1["is_cached"] is False

    # Second call with same idempotency key
    receipt2 = exec_service.execute_approval(app_id, idempotency_key="idem-key-repeat")
    assert receipt2["status"] == "succeeded"
    assert receipt2["is_cached"] is True
    assert receipt2["execution_id"] == receipt1["execution_id"]


def test_concurrent_stock_adjustment_and_negative_stock():
    b_id = uuid4()
    v_id = uuid4()
    p_id = uuid4()

    variant = ProductVariant(
        id=v_id,
        business_id=b_id,
        product_id=p_id,
        stock=10,
        stock_version=1,
    )
    db = MemoryDbSession([variant])
    repo = VariantRepository(session=db, business_id=b_id)

    # Concurrent attempt with stale stock_version fails
    with pytest.raises(StaleVersionError) as exc:
        repo.adjust_stock(variant_id=v_id, delta=5, expected_stock_version=99)
    assert "stock_version" in str(exc.value)

    # Negative resulting stock rejected
    with pytest.raises(InvalidStateError) as exc:
        repo.adjust_stock(variant_id=v_id, delta=-20, expected_stock_version=1)
    assert "negative" in str(exc.value)

    # Valid adjustment succeeds and increments stock_version
    updated = repo.adjust_stock(variant_id=v_id, delta=-3, expected_stock_version=1)
    assert updated.stock == 7
    assert updated.stock_version == 2
