"""Node 12: bounded repair; no model call is required for deterministic corrections."""

from app.agents.state import GraphState


def repair_or_escalate(state: GraphState) -> dict[str, object]:
    retries = state.get("retry_count", 0)
    if retries >= state.get("max_retries", 2):
        return {
            "status": "blocked",
            "error_code": "retry.cap_reached",
            "error_message": "Verification could not be repaired automatically; please review manually.",
        }
    return {
        "retry_count": retries + 1,
        "status": "awaiting_approval",
        "error_message": "A claim or consistency issue needs owner review.",
    }
