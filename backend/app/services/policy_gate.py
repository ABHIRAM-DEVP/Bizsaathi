"""Pure deterministic policy gate; models cannot override its decision."""

from app.agents.models import PolicyDecision


def evaluate_action(*, action: str, tenant_matches: bool, claim_overall: str | None = None) -> PolicyDecision:
    if not tenant_matches:
        return PolicyDecision(
            decision="deny", rule="tenant.cross_access_blocked", reason="Tenant mismatch.", evidence_ids=[]
        )
    if action in {"payment_write", "publish"}:
        return PolicyDecision(
            decision="deny",
            rule="policy.publish_without_approval" if action == "publish" else "policy.payment_write_denied",
            reason="Agents cannot publish or write payment status.",
            evidence_ids=[],
        )
    if claim_overall in {"fail", "needs_owner"}:
        return PolicyDecision(
            decision="deny",
            rule="claim.contradicted" if claim_overall == "fail" else "claim.unverified",
            reason="Claims require correction or owner confirmation.",
            evidence_ids=[],
        )
    return PolicyDecision(
        decision="require_approval", rule="approval.required", reason="Owner approval is required.", evidence_ids=[]
    )
