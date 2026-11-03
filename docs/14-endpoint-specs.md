# 14 Endpoint specifications (base path /v1)

Design document: request/response shapes are DESIGN PROPOSALS for you to confirm (ASSUMPTION), not facts about any external system. Classes (MVP, MVP-next, STRETCH, FUTURE) match docs/08-api-spec.md. Every endpoint has an ID (EP-xxx) that task files and prompts cite. Meta API specifics are not defined here (see docs/12).

## Global conventions
- Format: JSON, UTF-8. IDs: uuid. Timestamps: ISO 8601 UTC.
- Auth: `owner` routes need a valid session (HttpOnly cookie; CSRF protection for cookie auth; dev stub only when ENV=dev). Public store/catalog reads are anonymous; customer chat routes require the separate opaque, HttpOnly customer-account cookie. Roles: `owner`, `operator` (read-only on owner data, ASSUMPTION), `public`.
- Tenancy: business_id comes from the session or store slug, never from the request body. Cross-tenant ids return 404.
- Errors (problem JSON): `{type, title, status, detail, request_id, errors?[]}`. Codes used: 400, 401, 403, 404, 409 (conflict/stale version/idempotency), 413, 415, 422, 429, 501 (not built), 503 (model/provider unavailable, safe state).
- Pagination: `?limit=20` (max 100) and `?cursor=`; response `{items[], next_cursor}`.
- Idempotency: header `Idempotency-Key` required on endpoints marked [IDEM]. Same key + same body returns the original result; same key + different body returns 409.
- Optimistic concurrency: `If-Match: <version>` on endpoints marked [VER]; stale returns 409.
- Jobs: long work returns `202 {job_id, status_url:/v1/jobs/{id}, events_url:/v1/jobs/{id}/events}`. Job status: queued, running, awaiting_approval, succeeded, blocked, failed, cancelled.
- Provenance on AI-derived fields: `{value, source: "confirmed"|"ai_suggested", confidence?, evidence_ids?}`. Price and stock are never ai_suggested into a confirmed record: the seller must enter or confirm them.
- Audit: every state-changing owner action and every block/deny writes an audit event (actor, action, entity, detail, request_id).
- Rate limits: public routes and OTP send/verify always limited; others have a generous default (TODO tune).
- Logging: no secrets, no raw model reasoning, PII redacted.

## EP-H: Health (not in the earlier list; needed for deploy)
- EP-H01 `GET /health` public. 200 `{status:"ok"}`. No dependencies checked.
- EP-H02 `GET /health/ready` public. 200 if DB reachable (and Redis if enabled); 503 otherwise with `{checks:{db,redis}}`. No secrets or versions leaked.

## A. Authentication, seller, business
- EP-A01 `POST /auth/otp/send` public, MVP (dev mock). Body `{phone}` (E.164). Always 202 `{status:"sent"}` (no user enumeration). Dev mode logs the OTP to server console labelled DEV; real SMS is FUTURE. Limit 5/hour per phone and per IP. Errors 422, 429. Tests: 202 for unknown and known phone alike; 6th request in an hour gets 429.
- EP-A02 `POST /auth/otp/verify` public, MVP. Body `{phone, code}`. 200 sets session cookie, returns `{user, business}`; first successful login for a new phone creates a user and an empty business (ASSUMPTION). Lockout after 5 wrong codes for 15 min. Errors 401, 422, 429. Tests: wrong code 401; lockout; replayed code 401.
- EP-A03 `POST /auth/refresh` owner, MVP. 200 rotates session; old session invalid. 401 when expired/revoked.
- EP-A04 `POST /auth/logout` owner, MVP. 204; clears the browser session cookie. Idempotent.
- EP-A05 `GET /me` owner, MVP. 200 `{id, role, business_id, display_name, language}`.
- EP-A06 `PATCH /me` owner, MVP. Body subset of `{display_name, language}`. 200 updated user. 422 unknown language.
- EP-A07 `GET /business` owner, MVP. 200 `{id, name, slug, description, languages[], policies[{kind, version, body}]}`.
- EP-A08 `PATCH /business` owner, MVP. Body subset of `{name, slug, description, languages, policies[]}`. Slug unique and url-safe (409 if taken). A policy change creates a NEW policy version (old versions stay for evidence). Audit event. Tests: policy edit increments version; evidence referencing v1 still resolves.
- EP-A09 `PUT /business/payment-details` FUTURE: 501 with problem JSON "not implemented". Step-up auth design deferred.
- EP-A10 `POST /business/verification`, EP-A11 `GET /business/verification/status` FUTURE: 501. Never show a verified badge without a real process.
- EP-A12 `POST /auth/local/register` development-only. Body `{owner_name, business_name, email, password}`; creates an isolated local business and owner, stores a normalized email and bcrypt password hash, then sets a signed HttpOnly `SameSite=Strict` persistent cookie (400-day browser max-age). Passwords are at least 6 characters and at most 72 UTF-8 bytes. The signed token has no server-side expiry. Returns `{user, business: {id, name, slug}}` so the owner can open the dedicated shop URL. 403 outside `ENV=dev`; 422 for invalid input; 409 for an existing email. Credentials are never returned or stored in browser storage. Sessions remain valid while the owner and active business exist, the signing secret is unchanged, and the account's session version has not been incremented by logout. Legacy signed tokens default to session version zero.
- EP-A13 `POST /auth/local/login` development-only. Body `{email, password}`; normalizes email, verifies the password hash, and sets the same persistent HttpOnly session cookie for the account's business. Returns `{user, business: {id, name, slug}}`; invalid credentials return a generic 401. 403 outside `ENV=dev`; 422 for invalid input. `POST /auth/logout` increments the local account's session version when a valid cookie is present, invalidating all of that owner's local sessions, and clears the browser cookie.

## B. Media, catalogue, stock, jobs
- EP-B01 `POST /uploads` owner, MVP. Body `{kind: "photo"|"audio", mime, size_bytes, sha256?}`. 201 `{upload_id, method:"PUT", url, headers, expires_at}`. Rules: mime allowlist (photo: jpeg, png, webp; audio: mp3, wav, mp4/m4a; ASSUMPTION), size cap (default 10 MB, ASSUMPTION), key `business_id/uploads/<uuid>` server-generated, URL valid ~10 min. Content is verified when first used (EP-B02): object exists, size matches, magic-byte sniff matches mime. Errors 415, 413, 422. Tests: .exe renamed .jpg rejected at use; oversize 413; key prefixed with tenant.
- EP-B02 `POST /products/from-photo` owner, MVP, [IDEM]. Body `{upload_ids[1..4], seller_note?, language?}`. 202 job. Job result is a `product_draft` proposal (AI suggestions with uncertainty flags, conflicts vs existing SKUs). Never writes a product. Errors 404 (upload not yours), 422 (sniff failed), 409 (idempotency mismatch), 503 (model unavailable -> job ends `failed`/`blocked` with a manual path). Tests: 202 returned before the model call completes; conflict created, nothing overwritten.
- EP-B03 `POST /products/from-voice` owner, STRETCH, [IDEM]. Body `{audio_upload_id, photo_upload_ids?[], language_hint?}`. 202 job: transcribe, interpret, merge into a draft with transcript spans. Spoken price/stock become suggestions requiring seller confirmation.
- EP-B04 `GET /products` owner, MVP. Query `status, q, sku, low_stock, limit, cursor`. 200 `{items[], next_cursor}` tenant-scoped; each item `{id, sku, name, price_inr, status, stock_total, thumbnail_url}`.
- EP-B05 `POST /products` owner, MVP, [IDEM]. Two modes. Manual: `{sku?, name, description?, price_inr, variants[{color?,size?,stock}], media_ids[]}`. From draft: `{proposal_id, proposal_version, confirmed:{name, price_inr, variants[...]}}` where price and stock are supplied or explicitly confirmed by the seller. 201 `{id,...}` (from-draft creation goes through the approval/execution path, EP-D). Errors 422, 409 (sku exists, stale proposal). Tests: model-suggested price without seller confirmation rejected.
- EP-B06 `GET /products/{id}` owner, MVP. 200 product with per-field provenance, variants with `stock_version`, media with short-lived signed URLs, open `conflicts[]`. 404 cross-tenant.
- EP-B07 `PATCH /products/{id}` owner, MVP, [VER]. Partial confirmed fields. Stock cannot change here (use EP-B09). Price change writes an audit event with old and new values. 409 on stale version. Tests: stale 409; cross-tenant 404; price audit.
- EP-B08 `DELETE /products/{id}` owner, MVP. Soft delete (archive). 409 if open orders reference it. 204. Hard delete is not offered.
- EP-B09 `POST /products/{id}/stock` owner, MVP, [IDEM]. Body `{variant_id, delta | set_to, reason, expected_stock_version}`. 200 `{variant_id, stock, stock_version}`. 422 if result would be negative; 409 if expected version is stale. Audit event. Tests: concurrent adjustments; replayed idempotency key does not double-apply.
- EP-B10 `GET /jobs/{id}` owner, MVP. 200 `{id, kind, status, progress{step,total}, result_ref?, error?{code,message}, budget{model_calls, max_model_calls}, created_at, finished_at?}`. 404 cross-tenant.
- EP-B11 `GET /jobs/{id}/events` owner, MVP. `text/event-stream`. Event types: `step_started, step_finished, conflict_found, awaiting_approval, blocked, done, error`, heartbeat every 15 s, supports `Last-Event-ID` resume. Payloads contain observable data only. Tenant check on connect.

## C. Content studio and claim verification
- EP-C01 `POST /posts/generate/{product_id}` owner, MVP. Body `{channel: "instagram"|"whatsapp_status"|"facebook"|"generic", language: "en"|"hi"|"mr"}`. Preconditions: tenant-owned active product with confirmed name and positive price. Generation receives the seller-saved product description and attributes as untrusted source data, extracts only explicitly stated product features for two creative lines, and keeps those claims unverified with source evidence IDs. Returns 201 with a saved draft, provenance (`mode: "live"|"mock"`), and claims. Catalog name and price are inserted server-side with evidence IDs. A generated hook containing a price or number is rejected. Errors 404, 409 (product not ready or changed during generation), 422, 502 (model failure).
- EP-C07 `POST /posts/generate/{product_id}/stream` owner, MVP. Body matches EP-C01. Returns `text/event-stream`: `status`, `token` (unverified creative-line snapshot), `complete` (the validated and persisted EP-C01 draft), or `error`; sends a 15-second heartbeat. Live generation requests streaming JSON with at most 2,048 output tokens, a 10-second connect timeout, no read timeout, and no retry. Request-send and connection-pool timeouts remain bounded. Token previews are suggestions only and are not saved or verified until `complete`.
- EP-C09 `POST /posts/generate/{product_id}/quick` owner, MVP. Body matches EP-C01. Returns a saved three-line draft immediately using fixed English, Hindi, or Marathi local templates and tenant-confirmed product name/price; makes no AI-provider call and labels provenance as `mock` with model ID `quick-local-template-v1`. Creative copy remains unverified and requires owner review.
- EP-C02 `GET /posts` owner, MVP. Query `product_id, status(draft|checked|pending_approval|approved|exported), limit, cursor`.
- EP-C03 `GET /posts/{id}` owner, MVP. 200 `{id, product_id, channel, language, text, version, status, claims[], provenance{model_id, prompt_version, generated_at, mode:"live"|"mock"}, last_check?}`.
- EP-C04 `PATCH /posts/{id}` owner, MVP, [VER]. Body `{text}`. New version; previous claim-check and approvals are invalidated; status returns to `draft`. 409 if stale.
- EP-C05 `POST /posts/{id}/claim-check` owner, MVP. Body `{version}` (must be the current version). 200 (or 202 job if slow) `{post_id, version, claims:[{id, text, verdict:"supported"|"contradicted"|"unverified", severity, evidence:[{id, source_kind, source_id, source_version}], repair_suggestion?}], summary{supported, contradicted, unverified}, overall:"pass"|"fail"|"needs_owner"}`. Never a bare `safe:true`. Tests: contradicted claim -> fail; no-evidence claim -> unverified/needs_owner; stale version 409.
- EP-C06 `POST /posts/{id}/submit` owner, MVP. Body `{version}`. Requires a claim-check for that exact version with no contradicted claims; unverified claims block unless the owner edits them out (fail closed). 201 `{approval_id}`. 409 if no matching check.
- EP-C07 `POST /posts/{id}/share-status` owner, STRETCH. Body `{channel, status:"shared"|"skipped", note?}`. Only for approved posts. Records the owner's manual sharing; makes NO external call.
- EP-C08 `GET /posts/{id}/export` owner, STRETCH. Approved posts only (409 otherwise). 200 text plus short-lived media URLs.

## D. Approvals and execution
Approval types: `product_create, product_update, post_publish, order_action, reply`.
- EP-D01 `GET /approvals` owner, MVP. Query `type, status(pending|approved|rejected|expired|invalidated), limit, cursor`.
- EP-D02 `GET /approvals/{id}` owner, MVP. 200 `{id, type, status, proposal{id, version, payload, diff{before, after}}, evidence[], warnings[], risk, side_effect{description, reversible}, expires_at}`.
- EP-D03 `POST /approvals/{id}/approve` owner, MVP, [IDEM]. Body `{proposal_version}`. The policy gate runs again at execution time. 200 `{execution_id, status:"succeeded"|"failed", result_ref}`. 409 if the proposal version changed or approval is invalidated/expired; 403 for non-owner; 422 if the gate now denies. Tests: edit-after-view then approve -> 409; replay with same key -> same receipt, one side effect.
- EP-D04 `POST /approvals/{id}/reject` owner, MVP. Body `{reason?}`. 200. Audit event.
- EP-D05 `POST /approvals/{id}/edit` owner, MVP, [VER]. Body `{payload_patch, proposal_version}`. Creates a new proposal version, invalidates old approvals, re-runs the checks as a job. 202 job.

## E. Public store and customer chat (rate limited, authenticated customer accounts)
- EP-E01 `GET /public/stores/{slug}` public, MVP-next. 200 `{business{name,slug,description}, products[{id,name,price_inr,in_stock,image_url}]}` active products only; no PII. 404 for unknown slug. Cacheable ~60 s. Rate limit 120/min/IP.
- EP-E02 `POST /public/customer-accounts/register` public. Body `{email, display_name, password}`; minimum 12-character password. Requires `Origin` from `CORS_ALLOWED_ORIGINS` and `X-Customer-Request: 1`. Email is normalized; duplicate email returns 409. Registration sets a 30-day HttpOnly customer session cookie. Limit 5/hour/IP. Email verification and password recovery are not implemented.
- EP-E03 `POST /public/customer-accounts/login` public. Body `{email, password}`; requires the same origin and request marker; sets the same HttpOnly customer session cookie. Invalid credentials return a generic 401. Limit 10/15min/IP. `GET /public/customer-accounts/me` returns the signed-in customer profile (60/min/IP); `POST /public/customer-accounts/logout` revokes the current session and requires the origin and request marker (30/min/IP).
- EP-E04 `POST /public/stores/{slug}/sessions` requires a customer account session cookie plus the configured origin and request marker. Creates or resumes that customer's open conversation for the store and returns its message history; session ownership is enforced server-side. Rate limit 10/hour/IP.
- EP-E05 `POST /public/sessions/{id}/messages` requires the customer account cookie, configured origin and request marker, and a session owned by that account. Body `{text}` (1 to 1000 chars). 202 `{message_id, assistant_message?, escalated}`. A deterministic LangGraph workflow triages sensitive requests, reads tenant catalog facts, drafts a response, and verifies factual evidence. It answers confirmed price, stock, and description questions and can recommend listed products. Unsupported questions, refunds, payment/order actions, and safety requests escalate. No external model call or side effects. Limits 60/min/IP and 20/min/customer account. Tests: prompt injection cannot change catalog facts; another account cannot use the session.
- EP-E06 `GET /public/sessions/{id}/stream` requires the customer account cookie and an account-owned session. Events contain assistant replies, owner replies sent in the in-app customer chat, and escalation status. Limit 10/hour/IP.
- EP-E07 `POST /public/sessions/{id}/verify-phone/send`, `.../verify` FUTURE: 501.
- EP-E08 `POST /public/sessions/{id}/order` public, MVP-next, [IDEM]. Body `{items[{variant_id, qty}], customer_name, delivery_note?, consent:true}`. 201 order DRAFT. Prices come from the database, never from the client. 409 insufficient stock; 422 if consent is not true. No payment taken.
- EP-E09 `GET /widget.js` public, STRETCH. Static loader reading `data-store="<slug>"`; contains no secrets; served with a strict CSP note.

## F. Owner inbox and customers
- EP-F01 `GET /conversations` owner, MVP-next. Query `status(open|escalated|closed), limit, cursor`. Tenant-scoped; includes source (`public|demo`) and synthetic customer label where applicable.
- EP-F02 `GET /conversations/{id}` owner, MVP-next. 200 messages, escalation reason, linked evidence IDs. Tenant-scoped; cross-tenant IDs return 404.
- EP-F03 `POST /conversations/{id}/reply` owner, MVP-next. Body `{text}`. 201 persists an owner message in the tenant-owned conversation; public conversations return `delivery_status:"delivered"` when the reply is available in the authenticated customer chat and SSE stream. Synthetic demo conversations return `delivery_status:"not_sent"`. No external provider delivery. Audit event.
- EP-F04 `POST /conversations/{id}/block` owner, STRETCH. Body `{reason}`. Session token revoked.
- EP-F05 `GET /customers/{id}` owner, STRETCH. Phone and address masked by default; unmask is an audited action.
- EP-F06 `POST /conversations/demo/start` owner, dev/test only. Idempotently seeds three clearly synthetic conversations and, only if the tenant catalog is empty, a clearly labeled sample product. Production returns 403.
- EP-F07 `POST /conversations/demo/simulate` owner, dev/test only. Adds one longer synthetic customer message to the next of three demo threads, incorporating at most 180 characters from the tenant's active product description. Production returns 403; no external message is sent.
- EP-F08 `GET /businesses/me` owner, MVP. Returns the authenticated tenant's public store identity `{id,name,slug}` for constructing same-origin customer chat links.
- Customer messages appear as unread inbox items until the owner opens the conversation; opening it marks customer messages as read.
- EP-F07 `POST /conversations/{id}/demo-messages` owner, dev/test only. Body `{text}`. Adds a synthetic customer message and a catalog-grounded assistant reply or escalation; demo conversations only. No external send.

## G. Orders and payments
State machine: DRAFT -> AWAITING_PAYMENT -> PAID -> FULFILLED; also CANCELLED, FAILED. DRAFT -> AWAITING_PAYMENT happens when the owner approves an `order_action` (EP-D03). Only the execution service changes state.
- EP-G01 `GET /orders` owner, MVP. Query `status` (optional order state) and `limit` (1–100, default 50). Returns tenant-scoped orders with catalog item names, quantities and database prices. Synthetic demo examples are explicitly marked.
- EP-G02 `GET /orders/{id}` owner, MVP-next. 200 items, totals, status history, audit pointers.
- EP-G03 `POST /orders/{id}/confirm-payment` owner, MVP-next (simulated), [IDEM]. Body `{method:"cash"|"upi"|"bank"|"other", reference?, amount_inr}`. Only from AWAITING_PAYMENT; amount must equal total (422). Recorded as "owner-recorded, not provider-verified". Agents can never call this. 409 wrong state.
- EP-G04 `POST /orders/{id}/remind` owner, STRETCH. Stores an owner-authored reminder; no external send.
- EP-G05 `POST /orders/{id}/ship` owner, STRETCH. Only from PAID; body `{carrier?, tracking?}`. 409 otherwise.
- EP-G06 `POST /payments/link` FUTURE: 501.

## H. Trust, safety, audit
- EP-H03 `GET /audit-log` owner/operator, MVP. Query `actor, action, entity_type, entity_id, from, to, limit, cursor`. Append-only; no mutation endpoints.
- EP-H04 `GET /guardrail/events` owner/operator, MVP. Verdicts, blocks and denies with node, rule, evidence ids.
- EP-H05 `POST /reports`, EP-H06 `GET /disputes`, `POST /disputes`, `POST /disputes/{id}/respond` FUTURE: 501.

## I. Dashboard, channels, notifications
- EP-I01 `GET /dashboard` owner, MVP. 200 `{pending_approvals, open_escalations, recent_jobs[], low_stock[], next_step{label, route}}`.
- EP-I02 `GET /channels` owner, STRETCH. Static list with status `not_connected` or `unavailable`. Never reports a channel as connected.
- EP-I03 `POST /channels/{type}/connect` FUTURE: 501. EP-I04 `POST /push/subscribe` FUTURE: 501.
- EP-I05 `GET /notifications` owner, STRETCH. In-app notifications (approvals, escalations).
- EP-I06 `POST /webhooks/whatsapp|instagram|facebook` FUTURE: 501 until a real signed round-trip is tested.

## J. Observability and evaluation
- EP-J01 `GET /jobs/{id}/trace` owner/operator, MVP. Sanitized ordered events `{seq, node, event, tool?, redacted_input?, redacted_output?, evidence_ids?, decision?, retry?, duration_ms, error_code?}`. Never raw reasoning.
- EP-J02 `GET /evidence/{id}` owner/operator, MVP. `{id, source_kind, source_id, source_version, snapshot(redacted), claim_ids[]}`. Tenant-checked.
- EP-J03 `POST /evaluations/runs` owner, STRETCH. Body `{mode:"mock"|"live", split, system:"A"|"B"|"C", confirm_cost?}`. `live` requires `confirm_cost:true`. 202 job. Result labelled mock or live.
- EP-J04 `GET /evaluations/runs`, EP-J05 `GET /evaluations/runs/{id}` owner/operator, STRETCH. Metrics, failure cases, model ids, usage, cost, label.
- EP-J06 `GET /metrics/agents?days=30` owner/operator, STRETCH. `days` is 1-90. Returns tenant-scoped job counts by status, succeeded/terminal-job ratio, job-duration p50/p95, graph-node execution/error counts and duration p50/p95, and recorded model-call totals. Token counts and estimated cost are `null` until actual provider usage and pricing are recorded; no values are inferred. Queries are bounded by job creation time and business_id. Tests: owner/operator success; unauthenticated and public access denied; invalid window rejected; tenant filter applied.

## Coverage check
Every endpoint in docs/08-api-spec.md appears here. FUTURE routes return 501 with problem JSON. Keep this file and 08 in step; a new route needs both, plus an ADR if it adds a permission.
