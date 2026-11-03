"""Unit tests for Post generation, claim linking, and deterministic price verification (T-204)."""

import pytest

from app.agents.nodes.node_07_brief import create_brief
from app.agents.nodes.node_08_draft import draft_post
from app.agents.models import ContextBundle, InputBundle
from app.agents.state import GraphState


@pytest.mark.anyio
async def test_post_drafting_produces_claims_with_product_field_pointers(monkeypatch):
    from app.ai.mock import MockModelClient

    monkeypatch.setattr("app.agents.nodes.node_08_draft.get_model_client", lambda: MockModelClient())
    state: GraphState = {
        "extracted_fields": {
            "brief": {
                "channel": "instagram",
                "product_name": "Handmade Silk Saree",
                "price_inr": 2999.00,
            }
        },
        "model_calls": 0,
        "max_model_calls": 2,
    }

    res = await draft_post(state)
    assert res["status"] == "succeeded"
    claims = res["extracted_fields"]["claims"]
    assert len(claims) >= 2

    # Verify fact claim references price_inr
    fact_claims = [c for c in claims if c["kind"] == "fact"]
    assert len(fact_claims) > 0
    price_claim = next((c for c in fact_claims if c["source_field"] == "price_inr"), None)
    assert price_claim is not None
    assert "₹2999.00" in price_claim["text"]


@pytest.mark.anyio
async def test_deterministic_check_rejects_hallucinated_price(monkeypatch):
    from app.ai.interface import ModelClient

    class HallucinatingModel(ModelClient):
        async def generate_structured(self, prompt, schema, system_prompt=None):
            # Model hallucinates a price of 999 instead of 2999
            return {"creative_lines": ["Buy this saree for only Rs. 999 now!", "A thoughtful choice for every day."]}

        async def transcribe(self, audio_bytes, mime_type="audio/wav"):
            return ""

        async def generate_image(self, prompt):
            return b""

    monkeypatch.setattr("app.agents.nodes.node_08_draft.get_model_client", lambda: HallucinatingModel())

    state: GraphState = {
        "extracted_fields": {
            "brief": {
                "channel": "instagram",
                "product_name": "Handmade Silk Saree",
                "price_inr": 2999.00,
            }
        },
        "model_calls": 0,
        "max_model_calls": 2,
    }

    res = await draft_post(state)
    assert res["status"] == "failed"
    assert res["error_code"] == "claim.price_hallucinated"
    assert "disagrees with confirmed catalog price" in res["error_message"]


def test_post_brief_preserves_requested_language():
    state: GraphState = {
        "input_bundle": InputBundle(kind="post_generate", language="hi"),
        "context_bundle": ContextBundle(),
        "extracted_fields": {"channel": "instagram"},
    }

    result = create_brief(state)

    assert result["extracted_fields"]["brief"]["language"] == "hi"


@pytest.mark.anyio
async def test_post_draft_prompt_names_requested_language(monkeypatch):
    class CapturingModel:
        def __init__(self):
            self.prompt = ""

        async def generate_structured(self, prompt, schema, system_prompt=None):
            self.prompt = prompt
            return {"text": "खेळाचा प्रत्येक क्षण आनंदाने उजळवा."}

    client = CapturingModel()
    monkeypatch.setattr("app.agents.nodes.node_08_draft.get_model_client", lambda: client)
    state: GraphState = {
        "extracted_fields": {
            "brief": {
                "channel": "instagram",
                "product_name": "Demo Toy",
                "price_inr": 349.50,
                "language": "mr",
            }
        },
        "model_calls": 0,
        "max_model_calls": 2,
    }

    result = await draft_post(state)

    assert result["status"] == "succeeded"
    assert "Marathi (मराठी)" in client.prompt
    assert "Devanagari" in client.prompt
    assert len(result["extracted_fields"]["text"].splitlines()) == 3
