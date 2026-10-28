# 15 Schema, data types and formats (backend)

Authoritative for column types, enums, formats and envelopes. Supersedes the column names in docs/02-data-model.md (that file stays the overview/ER). Reference DDL: docs/schema/reference_schema.sql (design reference, not a migration, not yet run on a database). Endpoint behavior: docs/14-endpoint-specs.md. All shapes are design proposals (ASSUMPTION) until you accept them.

## 1. General rules
- Names: tables and columns `snake_case`; tables singular (`product`); money columns end `_inr`; booleans read as facts (`passed`); timestamps end `_at`; foreign keys `<table>_id`.
- JSON field names `snake_case`. No nulls for absent optional fields in requests; responses include documented fields, `null` only where the schema says nullable.
- Every business-owned table has `business_id uuid NOT NULL`; every query filters it. `otp_challenge` is the only non-tenant table in the reference schema.
- Enums are `text` + `CHECK` (easy to migrate), mirrored as Python `StrEnum` and TypeScript string unions generated from OpenAPI. Enum values lowercase, except order status (UPPERCASE as in the brief).
- Never `float` for money or stock. Never store secrets. Never store raw model reasoning.

## 2. Scalar types and formats
| Concept | Postgres | Python / Pydantic v2 | JSON | Rule |
|---|---|---|---|---|
| ID | `uuid` default `gen_random_uuid()` | `uuid.UUID` | string, canonical lowercase hyphenated | opaque; server-generated |
| Timestamp | `timestamptz` | `datetime` (tz-aware UTC) | ISO 8601 `2026-10-28T09:30:00Z` | naive datetimes rejected |
| Money (INR) | `numeric(12,2)` | `Decimal` (2 dp, `>= 0`) | string `"2499.00"` | never float; never a bare JSON number |
| Quantity / stock | `integer` | `int` (`>= 0`; order qty `1..100`) | number | stock changes only via stock endpoint |
| Version (concurrency) | `integer` from 1 | `int` | number; header `If-Match: 3` | increments on every confirmed change |
| Phone | `text` CHECK `^\+[1-9][0-9]{7,14}$` | `str` (E.164) | string | normalize before storing; masked in responses by default |
| Slug | `text` CHECK `^[a-z0-9][a-z0-9-]{1,62}$`, unique on `lower()` | `str` | string | url-safe |
| SKU | `text` CHECK `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`, unique per business | `str` | string | seller-visible |
| Language | `text` in `en, hi, mr` (extend deliberately) | `Literal["en","hi","mr"]` | string | BCP 47 primary subtag only |
| Free text | `text` with length CHECK | `str` with `max_length` | string | names 200, descriptions 5000, chat 1000 in, 4000 stored, notes 500 |
| Enum | `text` + CHECK | `StrEnum` | string | see section 3 |
| Hash | `bytea` (tokens, OTP) or `text` hex (sha256 of files) | `bytes` / `str` | hex string when exposed | only hashes of tokens are stored |
| Flexible object | `jsonb` | typed Pydantic model, `extra="forbid"` | object | jsonb columns always have a documented model (sections 6, 7) |
| Opaque token | not stored (hash only) | `str` (>= 32 random bytes, base64url) | string | returned once |
| Idempotency key | `text` CHECK `^[A-Za-z0-9_-]{8,64}$` | `str` | header `Idempotency-Key` | per business + endpoint |
| Pagination cursor | n/a | `str` | base64url of `{created_at, id}` | opaque to clients |
| Storage key | `text` | `str` | not exposed | `<business_id>/uploads/<uuid>`, server-generated |
| File hash | `text` CHECK 64 hex | `str` | string | sha-256 |

## 3. Enumerations
| Enum | Values |
|---|---|
| user.role | owner, operator |
| business.status | active, suspended |
| product.status | active, archived |
| policy.kind | delivery, returns, discounts, payment, other |
| media.kind / status | photo, audio, generated_image / pending, verified, rejected |
| job.kind | product_from_photo, product_from_voice, post_generate, claim_check, customer_reply, eval_run, proposal_revalidate |
| job.status | queued, running, awaiting_approval, succeeded, blocked, failed, cancelled |
| job_event.event | step_started, step_finished, conflict_found, awaiting_approval, blocked, retry, done, error |
| proposal.type | product_draft, product_create, product_update, post_publish, order_action, reply |
| proposal.status | draft, pending, approved, rejected, invalidated, expired, executed |
| approval.type | product_create, product_update, post_publish, order_action, reply |
| approval.status | pending, approved, rejected, expired, invalidated |
| approval.risk | low, medium, high |
| execution.status | succeeded, failed |
| post.channel | instagram, whatsapp_status, facebook, generic |
| post.status | draft, checked, pending_approval, approved, exported |
| claim.kind / verdict / severity | fact, opinion / supported, contradicted, unverified / low, medium, high |
| evidence.source_kind | product, variant, policy, order, transcript, media |
| public_session.status | open, escalated, closed, blocked |
| conversation.status | open, escalated, closed |
| message.role | customer, assistant, owner, system |
| order.status | DRAFT, AWAITING_PAYMENT, PAID, FULFILLED, CANCELLED, FAILED |
| order.payment_method | cash, upi, bank, other |
| audit.actor_type | user, agent, system, public |
| guardrail.decision | allow, require_approval, deny, block, escalate |
| eval.mode / split / system | mock, live / dev, heldout / A, B, C |
| model_usage.mode | live, mock |

Order transitions allowed (anything else is 409): DRAFT->AWAITING_PAYMENT (owner approves order_action), AWAITING_PAYMENT->PAID (owner confirm-payment), PAID->FULFILLED (ship), DRAFT|AWAITING_PAYMENT->CANCELLED, any non-terminal->FAILED. PAID, FULFILLED, CANCELLED, FAILED are terminal except PAID->FULFILLED.

## 4. Envelopes
List: `{"items":[...],"next_cursor":"<opaque>|null"}`.

Problem JSON (all errors):
```json
{"type":"https://bizsaathi.dev/problems/stale-version","title":"Stale version","status":409,
 "detail":"Post version 4 is current; request used 3.","request_id":"req_01H...","errors":[{"field":"text","message":"..."}]}
```
Error `type` slugs (extend as needed): validation-error, unauthenticated, forbidden, not-found, stale-version, idempotency-conflict, invalid-state, unsupported-media, payload-too-large, rate-limited, not-implemented, model-unavailable, policy-denied, evidence-missing.

Job accepted (202): `{"job_id":"<uuid>","status_url":"/v1/jobs/<id>","events_url":"/v1/jobs/<id>/events"}`.

SSE: `Content-Type: text/event-stream`; each message `id: <seq>`, `event: <type>`, `data: <json>`; heartbeat comment `: ping` every 15 s. Example `event: conflict_found` `data: {"field":"price_inr","values":[{"value":"2000.00","source":"voice"},{"value":"2499.00","source":"database"}]}`. Payloads contain observable data only.

Field with provenance (AI-derived values in drafts and product views):
```json
{"value":"cotton-silk blend","source":"ai_suggested","confidence":0.62,"evidence_ids":[]}
```
`source` is `confirmed` or `ai_suggested`. `confidence` is the model's or code's reported score, nullable, and is not a probability claim.

Evidence reference: `{"id":"<uuid>","source_kind":"product","source_id":"<uuid>","source_version":3}`.

Claim-check overall: `pass` (no contradicted, no unverified fact claims), `needs_owner` (unverified fact claims, no contradicted), `fail` (any contradicted).

Money in JSON is a string: `{"price_inr":"2499.00"}`.

## 5. Headers
`Idempotency-Key`, `If-Match` (version number), `X-Request-ID` (echoed; generated if absent), `X-Session-Token` (public chat), `Last-Event-ID` (SSE resume), `Retry-After` on 429 and 503.

## 6. Proposal payloads (jsonb `proposal.payload`, one model per `type`)
All have `schema_version: 1`, `extra="forbid"`, and `generated_by: {mode, model_ids[], prompt_version}`.

`product_draft` (AI suggestion only; never a fact):
```json
{"schema_version":1,
 "fields":{"name":{"value":"...","source":"ai_suggested","confidence":0.8},
           "attributes":{"color":{"value":"blue",...},"material":{"value":"cotton","source":"ai_suggested","confidence":0.4}}},
 "uncertainty":[{"field":"material","reason":"photo too blurry","ask_seller":true}],
 "conflicts":[{"field":"price_inr","values":[{"value":"2000.00","source":"voice"},{"value":"2499.00","source":"database"}],"severity":"high","needs_owner":true}],
 "matched_sku":"SAR-001","media_ids":["<uuid>"]}
```
Note: `price_inr` and stock may appear only as `conflicts` or seller-supplied values; a draft never carries a model-chosen price or stock as a fact.

`product_create` / `product_update`: `{"schema_version":1,"product":{sku,name,description?,price_inr,attributes,variants[{color?,size?,stock}]},"base_version":<int|null>,"seller_confirmed_fields":["price_inr","stock"]}`; the execution service rejects a payload where `price_inr` or stock is not in `seller_confirmed_fields`.

`post_publish`: `{"schema_version":1,"post_id":"<uuid>","post_version":<int>,"claim_check":{"overall":"pass","claim_ids":["<uuid>"]},"channel":"instagram"}`; approve means "owner approves this text for manual sharing" (no external call).

`order_action`: `{"schema_version":1,"order_id":"<uuid>","from":"DRAFT","to":"AWAITING_PAYMENT","total_inr":"4998.00","stock_check":{"ok":true,"as_of":"<ts>"}}`.

`reply`: `{"schema_version":1,"conversation_id":"<uuid>","text":"...","evidence_ids":["<uuid>"]}`.

Diff format (`approval.proposal.diff`): `{"before":{...},"after":{...},"changed":["price_inr","attributes.material"]}` using the same field paths.

## 7. Agent and trace formats
- Node input and output are Pydantic models in `app/agents/models/` (names from docs/10: `InputBundle`, `CandidateAttributes`, `ConflictRecord`, `ContentDraft`, `ClaimVerdict`; plus `TaskPlan`, `ContextBundle`, `PolicyDecision`, `RepairAction`).
- `PolicyDecision`: `{"decision":"allow|require_approval|deny","rule":"<id>","reason":"<user-readable>","evidence_ids":[]}`.
- Trace event (`job_event` and `GET /jobs/{id}/trace`): `{seq, node, event, tool?, redacted_input?, redacted_output?, evidence_ids[], decision?, retry?, duration_ms, error_code?}`; no reasoning text.
- Model usage record per call: `{node, model_id, mode:"live|mock", latency_ms, input_tokens?, output_tokens?, media_units?, est_cost_usd?}`; `est_cost_usd` is always labelled an estimate.
- Graph state limits: retries <= 2 per failing check; `max_model_calls` per job (default 8, config); timeout per model call (config).

## 8. Audit and guardrail formats
- `audit_event.action` is `entity.verb` in lowercase dotted form: `product.price_changed`, `product.stock_adjusted`, `post.edited`, `approval.approved`, `approval.rejected`, `order.payment_recorded`, `agent.action_denied`, `auth.login_failed`, `business.policy_versioned`.
- `detail` holds `{before?, after?, reason?, ids?}` with PII redacted; `actor_type` is `agent` only for denied or proposed actions, never for writes.
- `guardrail_event.rule` ids: `claim.contradicted`, `claim.unverified`, `crossmodal.mismatch`, `policy.payment_write_denied`, `policy.publish_without_approval`, `injection.suspected`, `tenant.cross_access_blocked`, `retry.cap_reached`, `model.unavailable`.
- `audit_event` is append-only (trigger in the reference schema). No update or delete endpoints.

## 9. Redaction rules (before logs, traces, model calls, audit detail)
- Phone: keep last 2 digits (`+91******21`). Address and delivery note: omitted from model prompts unless the node needs them. Customer name: first name only in prompts.
- Never include: secrets, tokens, session ids, OTP codes, signed URLs, storage keys.
- Test: a unit test feeds PII and secrets through the redactor and asserts the output.

## 10. Python conventions
- Pydantic v2 models: `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`; request models separate from response models; no ORM objects in responses; `Decimal` for money with `decimal_places=2`; `condecimal(ge=0)`.
- SQLAlchemy 2 typed `Mapped[...]` models, async sessions, one repository class per aggregate; repositories take `business_id` as a required argument.
- Modules: `app/schemas/<domain>.py` (API models), `app/models/<domain>.py` (ORM), `app/agents/models/` (graph models), `app/core/errors.py` (problem types), `app/core/formats.py` (validators: phone, slug, sku, money, language).
- Time: `datetime.now(UTC)`; never naive; clock injected in services for tests.
- IDs: generated in the database or `uuid4()`; never sequential identifiers exposed publicly.

## 11. OpenAPI conventions
`operationId` = `<verb><Resource>` (`createUpload`, `getJob`); one tag per domain (auth, business, products, jobs, posts, approvals, public, conversations, orders, audit, dashboard, evaluation); every route lists its error responses (problem JSON); `response_model` always set; examples on idempotent POSTs; contracts/openapi.json is committed and diffed by `just contract-check`.

## 12. Migration conventions (Alembic)
Revision message imperative (`add post and claim tables`); one concern per revision; autogenerate then edit; indexes named `<table>_<cols>_ix` / `_uq`; `CHECK` constraints named; never edit an applied revision; downgrade implemented and tested; data backfills in their own revision.

## 13. Config and env naming
`UPPER_SNAKE_CASE`, grouped by prefix: `DATABASE_`, `REDIS_`, `S3_`, `JWT_`, `META_`, `OTEL_`, `RATE_`. Required vars validated at startup in non-dev. Secrets only in env; `.env.example` lists names with empty values.

## 14. Logging format
One JSON object per line: `{ts, level, msg, request_id, business_id?, job_id?, node?, duration_ms?, error_code?}`. No bodies, no PII, no secrets.

## 15. Test data conventions
Synthetic only. Tenants named A and B in tests. Phones from a reserved fictional range in fixtures (TODO choose, e.g. `+91 00000 000xx` style placeholders that cannot be dialed). Mock-model fixtures labelled `mode: "mock"` everywhere they appear.
