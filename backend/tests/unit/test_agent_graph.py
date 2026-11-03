"""Unit tests for LangGraph runtime, typed state, trace events, and budgets (T-201)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.agents.models import InputBundle
from app.agents.runner import AgentJobRunner
from app.agents.tools import get_product_by_sku
from app.models.domain import Job, ModelUsage, Product


class MockDbSession:
    """Mock session tracking added items and scalar queries."""

    def __init__(self, entities=None):
        self.entities = entities or []
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

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
        for e in self.entities:
            # Check tenant isolation
            if hasattr(e, "business_id") and e.business_id in param_vals:
                if hasattr(e, "sku") and e.sku in param_vals:
                    matching.append(e)
                elif hasattr(e, "id") and e.id in param_vals:
                    matching.append(e)
                elif hasattr(e, "kind") and e.kind in param_vals:
                    matching.append(e)
                elif not any(k in ("sku", "id", "kind") for k in params.keys()):
                    matching.append(e)

        return ScalarResult(matching)


@pytest.mark.anyio
async def test_graph_runs_with_increasing_seq_and_no_raw_reasoning():
    b_id = uuid4()
    job_id = uuid4()

    job = Job(
        id=job_id,
        business_id=b_id,
        kind="product_from_photo",
        status="queued",
        max_model_calls=5,
    )
    mock_db = MockDbSession([job])

    runner = AgentJobRunner(session=mock_db, business_id=b_id)
    input_bundle = InputBundle(
        kind="product_from_photo",
        storage_keys=["uploads/test_photo.jpg"],
    )

    state = await runner.run_job(job_id=job_id, input_bundle=input_bundle)
    assert state["status"] in ("succeeded", "awaiting_approval")
    assert job.model_calls == state.get("model_calls", 0)

    # Verify JobEvent rows
    events = [item for item in mock_db.added if item.__tablename__ == "job_event"]
    assert len(events) >= 2

    node_events = [event for event in events if event.node not in ("system", "pipeline")]
    assert {event.node for event in node_events} >= {"planner", "intake", "context", "extract_photo"}
    assert all(event.duration_ms is not None and event.duration_ms >= 0 for event in node_events)
    assert all(event.event == "step_finished" for event in node_events)
    assert not any(isinstance(item, ModelUsage) for item in mock_db.added)

    # Check increasing sequence
    seqs = [ev.seq for ev in events]
    assert seqs == sorted(seqs)
    assert seqs[0] == 1

    # Check no raw reasoning
    for ev in events:
        if ev.redacted_output:
            assert "chain_of_thought" not in str(ev.redacted_output).lower()
            assert "raw_reasoning" not in str(ev.redacted_output).lower()


@pytest.mark.anyio
async def test_model_call_budget_exceeded_blocks_job():
    b_id = uuid4()
    job_id = uuid4()

    # Budget of 0 allowed model calls
    job = Job(
        id=job_id,
        business_id=b_id,
        kind="product_from_photo",
        status="queued",
        max_model_calls=0,
    )
    mock_db = MockDbSession([job])

    runner = AgentJobRunner(session=mock_db, business_id=b_id)
    input_bundle = InputBundle(
        kind="product_from_photo",
        storage_keys=["uploads/test_photo.jpg"],
    )

    state = await runner.run_job(job_id=job_id, input_bundle=input_bundle)
    assert state["status"] == "blocked"
    assert state.get("error_code") == "budget_exceeded"
    assert job.status == "blocked"
    assert "budget" in job.error_message.lower()


def test_readonly_tools_strictly_prevent_cross_tenant_leakage():
    tenant_a = uuid4()
    tenant_b = uuid4()

    prod_b = Product(
        id=uuid4(),
        business_id=tenant_b,
        sku="SKU-TENANT-B",
        name="Tenant B Secret Product",
        price_inr=Decimal("999.00"),
        status="active",
    )
    mock_db = MockDbSession([prod_b])

    # Tenant A attempts to fetch Tenant B's product by SKU
    leak_check = get_product_by_sku(mock_db, business_id=tenant_a, sku="SKU-TENANT-B")
    assert leak_check is None, "Tenant A MUST NOT access Tenant B product by SKU"

    # Tenant B fetches own product
    success_check = get_product_by_sku(mock_db, business_id=tenant_b, sku="SKU-TENANT-B")
    assert success_check is not None
    assert success_check["name"] == "Tenant B Secret Product"
