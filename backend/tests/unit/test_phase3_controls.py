"""Focused Phase 3 safety tests for deterministic verifier and policy controls."""

from decimal import Decimal
from uuid import uuid4

from app.agents.models import ContextBundle
from app.agents.nodes.node_11_critic import critique_consistency
from app.agents.nodes.node_12_repair import repair_or_escalate
from app.models.domain import Claim, Product
from app.services.claim_verifier import verify_claim
from app.services.policy_gate import evaluate_action


def product() -> Product:
    return Product(
        id=uuid4(), business_id=uuid4(), sku="KUR-1", name="Blue kurta", price_inr=Decimal("950.00"),
        attributes={"material": "cotton-silk blend", "color": "blue"}, field_sources={}, status="active", version=1,
    )


def test_silk_claim_is_contradicted_by_confirmed_material():
    claim = Claim(id=uuid4(), business_id=uuid4(), post_id=uuid4(), post_version=1, text="100% pure silk", kind="fact")
    verdict, severity, evidence, _ = verify_claim(claim, product())
    assert (verdict, severity) == ("contradicted", "high")
    assert evidence is not None


def test_superlative_fails_closed_as_unverified():
    claim = Claim(
        id=uuid4(),
        business_id=uuid4(),
        post_id=uuid4(),
        post_version=1,
        text="Best quality in India",
        kind="fact",
    )
    p = product()
    verdict, _, evidence, _ = verify_claim(claim, p)
    assert verdict == "unverified"
    assert evidence is None


def test_critic_flags_green_caption_for_blue_product():
    state = {
        "extracted_fields": {"text": "Beautiful green kurta"},
        "context_bundle": ContextBundle(matching_products=[{"color": "blue"}]),
    }
    result = critique_consistency(state)
    assert result["critique"]["severity"] == "high"


def test_repair_cap_blocks_after_two_attempts():
    state = {"retry_count": 2, "max_retries": 2}
    result = repair_or_escalate(state)
    assert result["status"] == "blocked"
    assert result["error_code"] == "retry.cap_reached"


def test_agent_payment_or_publish_is_denied():
    assert evaluate_action(action="payment_write", tenant_matches=True).decision == "deny"
    assert evaluate_action(action="publish", tenant_matches=True).decision == "deny"
