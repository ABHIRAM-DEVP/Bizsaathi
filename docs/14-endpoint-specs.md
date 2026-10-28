# 14 Endpoint specifications (base path /v1)

Design document: request/response shapes are DESIGN PROPOSALS for you to confirm (ASSUMPTION), not facts about any external system. Classes (MVP, MVP-next, STRETCH, FUTURE) match docs/08-api-spec.md. Every endpoint has an ID (EP-xxx) that task files and prompts cite. Meta API specifics are not defined here (see docs/12).

## Global conventions
- Format: JSON, UTF-8. IDs: uuid. Timestamps: ISO 8601 UTC.
- Auth: `owner` routes need a valid session (HttpOnly cookie; CSRF protection for cookie auth; dev stub only when ENV=dev). `public` routes need no login but use an opaque session token. Roles: `owner`, `operator` (read-only on owner data, ASSUMPTION), `public`.
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
- EP-A04 `POST /auth/logout` owner, MVP. 204; session revoked server-side. Idempotent.
- EP-A05 `GET /me` owner, MVP. 200 `{id, role, business_id, display_name, language}`.
- EP-A06 `PATCH /me` owner, MVP. Body subset of `{display_name, language}`. 200 updated user. 422 unknown language.
- EP-A07 `GET /business` owner, MVP. 200 `{id, name, slug, description, languages[], policies[{kind, version, body}]}`.
- EP-A08 `PATCH /business` owner, MVP. Body subset of `{name, slug, description, languages, policies[]}`. Slug unique and url-safe (409 if taken). A policy change creates a NEW policy version (old versions stay for evidence). Audit event. Tests: policy edit increments version; evidence referencing v1 still resolves.
- EP-A09 `PUT /business/payment-details` FUTURE: 501 with problem JSON "not implemented". Step-up auth design deferred.
- EP-A10 `POST /business/verification`, EP-A11 `GET /business/verification/status` FUTURE: 501. Never show a verified badge without a real process.

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
- EP-C01 `POST /products/{id}/posts/generate` owner, MVP, [IDEM]. Body `{channel: "instagram"|"whatsapp_status"|"facebook"|"generic", language, tone?, objective?}`. Preconditions: product active with confirmed name and price. 202 job; result is post draft v1 with a claim list (each claim marked fact or opinion). Errors 404, 409 (product not ready), 422, 503.
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

## E. Public store and customer chat (rate limited, opaque tokens)
- EP-E01 `GET /public/stores/{slug}` public, MVP-next. 200 `{business{name,slug,description}, products[{id,name,price_inr,in_stock,image_url}]}` active products only; no PII. 404 for unknown slug (same timing as valid). Cacheable ~60 s.
- EP-E02 `POST /public/stores/{slug}/sessions` public, MVP-next. 201 `{session_id, session_token, expires_at, disclosure:"You are chatting with an AI assistant for <store>"}`. Limit 10/hour/IP. The token is returned once and sent in header `X-Session-Token`.
- EP-E03 `POST /public/sessions/{id}/messages` public, MVP-next. Header token required. Body `{text}` (1 to 1000 chars). 202 `{message_id}`; reply arrives on EP-E04. Pipeline: node 09 -> 10 -> 13 with read-only tools. Limit 20/min/session. Errors 401, 404, 413, 422, 429. Tests: injection text does not change behavior; no business data from other tenants.
- EP-E04 `GET /public/sessions/{id}/stream` public, MVP-next. SSE events `reply{text, product_ids[]}`, `escalated{message}`, `closed`. Replies include only public-safe references.
- EP-E05 `POST /public/sessions/{id}/verify-phone/send`, EP-E06 `.../verify` FUTURE: 501.
- EP-E07 `POST /public/sessions/{id}/order` public, MVP-next, [IDEM]. Body `{items[{variant_id, qty}], customer_name, delivery_note?, consent:true}`. 201 order DRAFT `{order_id, status:"DRAFT", items[{variant_id, qty, unit_price_inr}], total_inr, notice:"Not confirmed until the seller confirms"}`. Prices come from the database, never from the client. 409 insufficient stock; 422 if consent is not true. Minimal PII; no payment taken.
- EP-E08 `GET /widget.js` public, STRETCH. Static loader reading `data-store="<slug>"`; contains no secrets; served with a strict CSP note.

## F. Owner inbox and customers
- EP-F01 `GET /conversations` owner, MVP-next. Query `status(open|escalated|closed), limit, cursor`.
- EP-F02 `GET /conversations/{id}` owner, MVP-next. 200 messages, escalation reason, linked evidence ids.
- EP-F03 `POST /conversations/{id}/reply` owner, MVP-next. Body `{text, suggested_reply_id?}`. The owner's submission is the approval. 201; delivered via the session stream. Audit event.
- EP-F04 `POST /conversations/{id}/block` owner, STRETCH. Body `{reason}`. Session token revoked.
- EP-F05 `GET /customers/{id}` owner, STRETCH. Phone and address masked by default; unmask is an audited action.

## G. Orders and payments
State machine: DRAFT -> AWAITING_PAYMENT -> PAID -> FULFILLED; also CANCELLED, FAILED. DRAFT -> AWAITING_PAYMENT happens when the owner approves an `order_action` (EP-D03). Only the execution service changes state.
- EP-G01 `GET /orders` owner, MVP-next. Query `status, limit, cursor`.
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
- EP-J06 `GET /metrics/agents` owner/operator, STRETCH. Per-node p50/p95 latency, error rate, retry count, model calls.

## Coverage check
Every endpoint in docs/08-api-spec.md appears here. FUTURE routes return 501 with problem JSON. Keep this file and 08 in step; a new route needs both, plus an ADR if it adds a permission.
