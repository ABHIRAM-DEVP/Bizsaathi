---
paths:
  - "apps/api/app/schemas/**"
  - "apps/api/app/models/**"
  - "apps/api/app/core/formats.py"
  - "apps/api/app/agents/models/**"
  - "apps/api/alembic/**"
---

# Schema and format rules
- docs/15-schema-and-formats.md is authoritative for types, enums, formats and envelopes; docs/14-endpoint-specs.md for endpoint behavior. If code needs something they do not define, update the doc (and an ADR if it changes a boundary) before coding.
- Money: `numeric(12,2)` in the database, `Decimal` in Python, a string in JSON. Never float.
- IDs uuid; timestamps timezone-aware UTC ISO 8601; enums are `text` + CHECK mirrored by `StrEnum`; order status is UPPERCASE, other enums lowercase.
- Pydantic v2 with `extra="forbid"`; separate request and response models; no ORM objects in responses; every jsonb column has a typed Pydantic model.
- Errors are problem JSON with `request_id` and a `type` slug from the doc. Lists use `{items, next_cursor}`. Long work returns 202 with job links.
- AI-derived fields carry provenance (`confirmed` or `ai_suggested`). A model never supplies price or stock as a confirmed fact; the execution service rejects payloads that lack `seller_confirmed_fields`.
- Trace, audit and log payloads are redacted and contain no reasoning text, secrets, tokens or signed URLs.
