---
paths:
  - "**/tests/**"
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/test_*.py"
  - "evals/**"
---

# Testing rules
- Failing test first for new behavior and bug fixes; show it fail for the right reason.
- Names state behavior: `test_tenant_b_cannot_read_tenant_a_product`.
- Every endpoint: success, 422, 401, 403 (wrong role or tenant), 404 where applicable.
- Agent nodes: happy path, schema-violating model output, tool failure, injection string, retry-cap termination, unauthorized action blocked.
- Unit: no network, no DB, milliseconds. Integration: real Postgres and Redis.
- Mock models only at the model boundary via the adapter. Mock results are labelled mock and never reported as live quality.
- Never delete, skip, xfail or loosen an assertion or eval threshold to get green. Explain and change it deliberately.
- Regression tests must fail on the old code; prove it.
- Flaky: fix the cause. No retries.
- Evals: see .claude/rules/evals.md.
