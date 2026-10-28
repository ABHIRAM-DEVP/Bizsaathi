---
paths:
  - "backend/app/agents/**"
  - "backend/tests/**/agents/**"
---

# Agent workflow rules (verifiable agents)
- Closed loop: perceive -> plan -> execute tools -> verify -> repair or escalate -> request approval -> execute -> measure.
- Separation of controls: evidence verifier (facts), multimodal critic (cross-modal consistency), policy gate (permissions and rules) are distinct. The writer never grades itself. A critic is "independent" only if evaluated against known errors; do not claim independence from a second prompt alone.
- Structured outputs only: every model call is parsed into a Pydantic model. Parse failure is a tool failure (bounded retry, then escalate), never "best effort" text.
- Claims: each factual claim -> verdict supported | contradicted | unverified, with evidence IDs and source versions. unverified blocks or escalates.
- Fail closed: missing evidence, tool error, model unavailable, or retry cap reached -> blocked/escalate with a user-readable reason. A fallback model never skips the same checks.
- Permissions are enforced in code outside the model. The model may propose an action; the policy gate returns allow | require_approval | deny; deny cannot be overridden by the model.
- Draft and commit are different actions. Side effects use idempotency keys and run only in the execution service after approval bound to a proposal version. Edited proposal invalidates the old approval.
- Budgets: max steps, max retries (2), max model calls per workflow, timeout per call. Record counts in state.
- No raw chain-of-thought in logs or traces. Record events: tool, redacted I/O, evidence IDs, decision, retries, duration, error code.
- Start simple: do not add a node, model call or agent debate unless an eval shows a failure it fixes.
