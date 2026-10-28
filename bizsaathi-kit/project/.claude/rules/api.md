---
paths:
  - "apps/api/app/routers/**"
  - "apps/api/app/services/**"
  - "apps/api/app/schemas/**"
---

# API rules
- Router -> service -> repository. A router parses input, calls one service method, returns a schema.
- Pydantic v2 schemas for all I/O. Never return ORM objects.
- Authorization (role + tenant) in the service layer for every resource access. Public routes are explicitly listed and rate limited.
- Domain exceptions from app/core/errors.py map to one problem-JSON handler with a request_id.
- Long work (photo, voice, content, claim checks) is a job: return a job id, expose /jobs/{id}, /jobs/{id}/events, /jobs/{id}/trace (sanitized).
- claim-check responses contain claim, verdict, evidence IDs, severity, repair suggestion. Never a bare `safe: true`.
- Approvals bind to a proposal version; edits invalidate approvals and re-run checks.
- Side effects need idempotency keys. Payment confirmation is owner-confirmed or provider-backed, never model-written.
- Redis keys: prefix + TTL, documented in docs/02-data-model.md.
- Priority classes in docs/08-api-spec.md: MVP, STRETCH, FUTURE. Do not build FUTURE routes; webhook routes stay 501 until verified.
