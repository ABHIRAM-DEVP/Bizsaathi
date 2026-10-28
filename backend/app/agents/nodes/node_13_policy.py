"""Node 13: policy decision is separate from writer and verifier."""

from app.agents.state import GraphState
from app.services.policy_gate import evaluate_action


def apply_policy_gate(state: GraphState) -> dict[str, object]:
    critique = state.get("critique", {})
    claims = state.get("extracted_fields", {}).get("claims", [])
    overall = "fail" if critique.get("mismatch") or any(c.get("verdict") != "supported" for c in claims) else "pass"
    decision = evaluate_action(action="post_submit", tenant_matches=True, claim_overall=overall)
    return {
        "policy_decision": decision,
        "status": "awaiting_approval" if decision.decision == "require_approval" else "blocked",
        "error_code": None if decision.decision == "require_approval" else decision.rule,
        "error_message": decision.reason,
    }
