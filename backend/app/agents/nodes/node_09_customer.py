"""Node 09: Customer Chat (Public-facing conversational assistant)."""

from typing import Any
from uuid import UUID

from app.agents.state import GraphState
from app.ai import get_model_client


async def process_customer_chat(state: GraphState) -> dict[str, Any]:
    """
    Generate a grounded response to a customer question.
    
    Flow:
    1. Retrieve customer message from input_bundle
    2. Load conversation history (if exists)
    3. Query product catalog for relevant context
    4. Generate response with evidence links
    5. Return response + evidence IDs
    
    This node NEVER commits data; it only generates proposals.
    The response is returned to the customer via the public API.
    """
    # Check budget
    current_calls = state.get("model_calls", 0)
    max_calls = state.get("max_model_calls", 8)
    if current_calls >= max_calls:
        return {
            "status": "blocked",
            "error_code": "budget_exceeded",
            "error_message": f"Model-call budget of {max_calls} exceeded.",
        }

    input_bundle = state["input_bundle"]
    business_id = state["business_id"]
    conversation_id = input_bundle.conversation_id
    customer_message = input_bundle.customer_message
    language = input_bundle.language or "en"

    if not customer_message:
        return {
            "status": "failed",
            "error_code": "customer_chat.missing_message",
            "error_message": "Customer message is required for customer_reply job",
        }

    # Get context bundle (product catalog, policies)
    context_bundle = state.get("context_bundle")
    if not context_bundle:
        # Node 03 should have populated this; if missing, escalate
        return {
            "status": "blocked",
            "error_code": "customer_chat.missing_context",
            "error_message": "Context bundle not loaded. Node 03 must run first.",
        }

    # Load conversation history if this is an ongoing conversation
    history_messages = []
    if conversation_id:
        # In real implementation, this would query Message table
        # For now, we simulate with state or skip
        history_messages = state.get("conversation_history", [])

    # Build prompt with context
    product_context = _format_product_context(context_bundle)
    policy_context = _format_policy_context(context_bundle)
    history_text = _format_history(history_messages)

    prompt = f"""You are a helpful store assistant. Answer the customer's question using ONLY the information provided below.

PRODUCT CATALOG:
{product_context}

STORE POLICIES:
{policy_context}

CONVERSATION HISTORY:
{history_text}

CUSTOMER QUESTION ({language}):
{customer_message}

Generate a helpful, friendly response in {language}. Include specific product names and prices when relevant. If the question cannot be answered with the available information, politely say so.

RULES:
- Use ONLY facts from the product catalog and policies above
- Do NOT invent prices, availability, or features
- Do NOT make promises about delivery or payment that are not in the policies
- If asked about products not in the catalog, say "We don't currently have that item"
- Be warm and helpful, but accurate
"""

    client = get_model_client()
    
    # Generate response (using generate_structured with simple schema for text response)
    schema = {
        "type": "object",
        "properties": {
            "response": {"type": "string"}
        },
        "required": ["response"]
    }
    
    result_obj = await client.generate_structured(prompt, schema)
    response_text = result_obj.get("response", "I'm here to help! What can I assist you with?")

    # Extract evidence: which products/policies were mentioned?
    evidence_ids = _extract_evidence_ids(response_text, context_bundle)

    # Build result
    result_payload = {
        "role": "assistant",
        "body": response_text,
        "evidence_ids": [str(eid) for eid in evidence_ids],
        "language": language,
    }

    return {
        "status": "running",
        "model_calls": current_calls + 1,
        "result": result_payload,
        "proposal_payload": result_payload,  # For approval flow if needed
    }


def _format_product_context(context_bundle: dict[str, Any]) -> str:
    """Format product list for prompt context."""
    products = context_bundle.get("matching_products", [])
    if not products:
        return "No products currently available."
    
    lines = []
    for p in products:
        name = p.get("name", "Unknown Product")
        price = p.get("price_inr", 0)
        desc = p.get("description", "No description available.")
        stock_info = ""
        if "stock" in p:
            stock = p["stock"]
            stock_info = f" (In stock: {stock})" if stock > 0 else " (Out of stock)"
        lines.append(f"- {name}: ₹{price}{stock_info}\n  {desc}")
    
    return "\n".join(lines)


def _format_policy_context(context_bundle: dict[str, Any]) -> str:
    """Format policy list for prompt context."""
    policies = context_bundle.get("policies", [])
    if not policies:
        return "No specific policies available. Please ask the store owner for details."
    
    lines = []
    for pol in policies:
        kind = pol.get("kind", "general")
        body = pol.get("body", "")
        lines.append(f"- {kind.upper()}: {body}")
    
    return "\n".join(lines)


def _format_history(history: list[dict[str, Any]]) -> str:
    """Format conversation history for prompt context."""
    if not history:
        return "(This is the first message in the conversation)"
    
    lines = []
    for msg in history[-5:]:  # Last 5 messages only
        role = msg.get("role", "unknown")
        body = msg.get("body", "")
        lines.append(f"{role.upper()}: {body}")
    
    return "\n".join(lines)


def _extract_evidence_ids(response: str, context_bundle: dict[str, Any]) -> list[UUID]:
    """
    Extract evidence IDs for products/policies mentioned in the response.
    
    Simple heuristic: if a product name appears in the response, link its evidence.
    In production, this should be more sophisticated (entity linking, etc.)
    """
    evidence_ids: list[UUID] = []
    
    products = context_bundle.get("matching_products", [])
    for p in products:
        product_name = p.get("name", "")
        if product_name.lower() in response.lower():
            # In real implementation, products would have evidence_id or source_id
            # For now, we use product_id as a placeholder
            if "id" in p:
                try:
                    evidence_ids.append(UUID(p["id"]))
                except (ValueError, TypeError):
                    pass
    
    # Similarly for policies
    policies = context_bundle.get("policies", [])
    for pol in policies:
        if "id" in pol:
            try:
                evidence_ids.append(UUID(pol["id"]))
            except (ValueError, TypeError):
                pass
    
    return evidence_ids
