"""Node 10: deterministic claim verifier; facts without proof fail closed."""

from app.agents.state import GraphState


def verify_claims(state: GraphState) -> dict[str, object]:
    claims = state.get("extracted_fields", {}).get("claims", [])
    checked = []
    has_failure = False
    for claim in claims:
        verdict = "supported" if claim.get("kind") == "fact" and claim.get("source_field") else "unverified"
        checked.append({**claim, "verdict": verdict})
        has_failure = has_failure or verdict != "supported"
    return {
        "extracted_fields": {**state.get("extracted_fields", {}), "claims": checked},
        "status": "running",
        "verification_failed": has_failure,
    }
