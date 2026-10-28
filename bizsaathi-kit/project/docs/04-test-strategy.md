# 04 Test strategy

## Layers and commands
| Layer | Tool | Where | Command | Notes |
|---|---|---|---|---|
| Repo guards | bash, python3 | scripts/ | `just guards` | secret scan + eval dataset validation |
| API unit | pytest | apps/api/tests/unit | `just check-fast` | no network/DB |
| Web unit/component | Vitest + Testing Library | apps/web | `just check-fast` | roles/labels |
| API integration | pytest + HTTPX + real Postgres/Redis | apps/api/tests/integration | `just check` | tenant, authz, uploads |
| Contract | OpenAPI diff | contracts/openapi.json | `just contract-check` | |
| Agent graph | pytest, mock adapter | tests/.../agents | `just check-fast` | routing, interrupts, retry caps |
| Evals (mock) | eval runner | evals/ | `just eval-mock` | plumbing only; not quality |
| Evals (live) | eval runner + Meta API | evals/ | `just eval-live` | costs credits, ask first |
| E2E + PWA | Playwright | apps/web/e2e | `just e2e` | mobile and desktop viewport, offline/reconnect |
| Smoke | curl | scripts/api_smoke.sh | `just smoke` | emoji reporter |
| Accessibility | axe via Playwright (TODO verify) | e2e | `just e2e` | |

## TDD loop
Acceptance lines -> failing tests -> implement -> `just check-fast` -> `just check` -> report with real output.

## Agent-specific tests (every node)
Schema-violating model output; tool failure; prompt-injection string in each untrusted input; retry-cap termination; unauthorized action blocked; approval interrupt resumes only with a matching proposal version; idempotent side effects (replay creates no duplicate).

## Backend security tests
Cross-tenant read/update/delete negatives; role checks; upload type/size/content; public endpoint rate limit; no secret in logs (assert redaction); payment status cannot be written by an agent path.

## AI evals
See evals/README.md and .claude/rules/evals.md. Compare A (single call), B (tools + evidence), C (full graph) on heldout cases. Metrics in evals/thresholds.yaml. Thresholds set before runs; TODO means baseline first. Keep mock and live separate and labelled.

## Production-readiness checklist (before demo)
- [ ] `just check` green on a clean clone
- [ ] Migrations apply on empty DB and downgrade one step
- [ ] Health endpoint, structured logs with request_id, per-node spans
- [ ] Every resource endpoint tested for 401, 403, cross-tenant
- [ ] Rate limits on public endpoints; upload limits
- [ ] No secrets in repo, frontend bundle, logs (`just guards`)
- [ ] Real Meta call verified with `just meta-smoke` and recorded in docs/12
- [ ] Live eval run recorded with date, model ids, usage; failures kept
- [ ] PWA installs on a phone-sized viewport; offline message verified
- [ ] Deployed URL verified with an actual request, or the demo says "local"
- [ ] Demo script rehearsed; mocks identified

## Honesty rule
A test counts only with its real output. "Should work" is not a result. Mock results never stand in for live-model quality.
