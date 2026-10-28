"""Unit tests for Node 09: Customer Chat."""

from uuid import uuid4

import pytest

from app.agents.models import InputBundle
from app.agents.nodes.node_09_customer import process_customer_chat
from app.agents.state import GraphState


@pytest.mark.anyio
async def test_customer_chat_basic_response():
    """Node 09 generates a response to customer question with evidence."""
    business_id = uuid4()
    job_id = uuid4()
    product_id = uuid4()

    # Setup context with product catalog
    context_bundle = {
        "matching_products": [
            {
                "id": str(product_id),
                "name": "Handwoven Cotton Saree",
                "price_inr": 2500,
                "description": "Beautiful traditional saree with handwoven patterns",
                "stock": 5,
            }
        ],
        "policies": [
            {
                "id": str(uuid4()),
                "kind": "delivery",
                "body": "Free delivery on orders above ₹2000. Delivery takes 3-5 business days.",
            }
        ],
    }

    state: GraphState = {
        "business_id": business_id,
        "job_id": job_id,
        "input_bundle": InputBundle(
            kind="customer_reply",
            customer_message="Do you have cotton sarees available?",
            language="en",
        ),
        "context_bundle": context_bundle,  # type: ignore
        "model_calls": 0,
        "max_model_calls": 8,
        "status": "running",
    }

    result = await process_customer_chat(state)

    assert result["status"] == "running"
    assert result["model_calls"] == 1
    assert "result" in result
    
    response = result["result"]
    assert response["role"] == "assistant"
    assert "body" in response
    assert len(response["body"]) > 0
    # Mock model returns generic response - just verify structure
    assert isinstance(response["body"], str)


@pytest.mark.anyio
async def test_customer_chat_missing_message():
    """Node 09 fails if customer message is missing."""
    state: GraphState = {
        "business_id": uuid4(),
        "job_id": uuid4(),
        "input_bundle": InputBundle(
            kind="customer_reply",
            customer_message=None,  # Missing!
            language="en",
        ),
        "context_bundle": {"matching_products": [], "policies": []},  # type: ignore
        "model_calls": 0,
        "max_model_calls": 8,
        "status": "running",
    }

    result = await process_customer_chat(state)

    assert result["status"] == "failed"
    assert result["error_code"] == "customer_chat.missing_message"


@pytest.mark.anyio
async def test_customer_chat_missing_context():
    """Node 09 blocks if context bundle not loaded."""
    state: GraphState = {
        "business_id": uuid4(),
        "job_id": uuid4(),
        "input_bundle": InputBundle(
            kind="customer_reply",
            customer_message="Hello?",
            language="en",
        ),
        # context_bundle missing!
        "model_calls": 0,
        "max_model_calls": 8,
        "status": "running",
    }

    result = await process_customer_chat(state)

    assert result["status"] == "blocked"
    assert result["error_code"] == "customer_chat.missing_context"


@pytest.mark.anyio
async def test_customer_chat_budget_exceeded():
    """Node 09 blocks if model call budget exceeded."""
    state: GraphState = {
        "business_id": uuid4(),
        "job_id": uuid4(),
        "input_bundle": InputBundle(
            kind="customer_reply",
            customer_message="Test message",
            language="en",
        ),
        "context_bundle": {"matching_products": [], "policies": []},  # type: ignore
        "model_calls": 8,  # Already at limit
        "max_model_calls": 8,
        "status": "running",
    }

    result = await process_customer_chat(state)

    assert result["status"] == "blocked"
    assert result["error_code"] == "budget_exceeded"
