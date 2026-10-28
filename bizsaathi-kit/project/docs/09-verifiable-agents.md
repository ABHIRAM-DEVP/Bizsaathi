# 09 Verifiable agents (Agents 102 concepts applied to BizSaathi)

Source note: the "Agents 102: Best Practices for Verifiable Agents" session could not be retrieved while building this kit (search found no transcript). This document encodes verifiable-agent principles from the project brief, the BizSaathi 2.0 plan, and a third-party agent best-practices page (claudskills.com, not the talk). When you have the session's notes or slides, reconcile this file with them and mark differences. Do not cite this as the talk's content.

## Principles -> mechanism -> test
| Principle | BizSaathi mechanism | Where | Test |
|---|---|---|---|
| Safety lives in code, prompts only describe intent | policy gate and tool permissions enforced server-side | node 13, tools | injection evals ev-006/007/015 |
| Every claim traceable | claim -> verdict -> evidence ids with source versions | node 10, EVIDENCE table | evidence coverage metric |
| Fail closed | missing evidence, tool error, model down, cap reached -> blocked/escalate | agents rules | ev-003, retry-cap test |
| Typed, narrow, auditable tools | Pydantic in/out; per-node permission set; denials return structured results | tools | schema-violation tests |
| Draft vs commit are separate | proposal (draft) vs execution service (commit) after owner approval | nodes 13-14 | ev-010, version-bound approval test |
| Separate generator from checker | writer 08; verifier 10; critic 11; gate 13 | catalog | routing tests |
| Bounded autonomy | budgets: max steps, 2 repairs, max model calls, timeouts | state | termination tests |
| Resumable state | LangGraph checkpoints; interrupts for approval | graph | resume test with version check |
| Observable, not introspective | events: tool, redacted I/O, evidence ids, decision, retries, duration, error code; no chain-of-thought | /jobs/{id}/trace | trace redaction test |
| Measurable done condition | acceptance criteria + `just check` + evals | tasks | CI |
| Idempotent side effects | Idempotency-Key on orders, approvals, notifications | execution service | replay test |
| Start simple, add agents only for measured failures | compare A (single call), B (tools), C (full graph) | evals | report incl. cases where C is worse |
| Treat inputs as hostile | customer text, transcripts, uploads, retrieved docs are data | all | injection suite |

## Verification ladder for any generated output
1. Schema validity (Pydantic). 2. Deterministic business rules (price, stock, state machine). 3. Evidence check per claim. 4. Cross-modal critic. 5. Policy gate (allow / require approval / deny). 6. Human approval bound to proposal version. 7. Audit event and metrics.

## What "verified" may and may not mean in the UI and demo
- Allowed: "Supported by product record SAR-001 (material)", "Unverified: needs your confirmation".
- Not allowed: a "verified seller" badge without a real process; "safe: true" without evidence; calling a mock a working integration.

## Anti-patterns to reject in review
- One LLM call that writes, checks and approves.
- Retrying until the check passes without a cap.
- Tuning prompts on the heldout set.
- Logging raw reasoning or secrets.
- Tools with unrestricted SQL or payment write.
