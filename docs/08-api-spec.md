# 08 API spec (base path /v1)

Per-endpoint behavior (request, response, errors, rules, tests) is in docs/14-endpoint-specs.md; types and formats in docs/15-schema-and-formats.md; `python3 scripts/check_docs.py` checks that every path here is specified there.
Classes (MVP / MVP-next / STRETCH / FUTURE) are ASSUMPTIONS to confirm. Agent nodes are internal, not endpoints. Build MVP first; do not build FUTURE routes (webhooks return 501).

## A. Auth, seller, business
| Method | Path | Purpose | Class |
|---|---|---|---|
| POST | /auth/otp/send | send OTP (dev: console/mock; real SMS FUTURE) | MVP (mock) |
| POST | /auth/otp/verify | verify, issue session | MVP |
| POST | /auth/refresh, /auth/logout | session lifecycle | MVP |
| POST | /auth/local/register | create an isolated local-development owner and business | dev only |
| POST | /auth/local/login | sign in to a local-development account | dev only |
| GET, PATCH | /me | seller profile | MVP |
| GET, PATCH | /business | shop profile, policies | MVP |
| PUT | /business/payment-details | payout details with step-up auth | FUTURE |
| POST, GET | /business/verification, /business/verification/status | verification | FUTURE (no verified badges without real process) |

## B. Media, catalogue, jobs
| Method | Path | Purpose | Class |
|---|---|---|---|
| POST | /uploads | signed upload URL | MVP |
| POST | /products/from-photo | start photo workflow (202 + job id) | MVP |
| POST | /products/from-voice | start voice workflow | STRETCH |
| GET, POST | /products | list, create from reviewed draft | MVP |
| GET, PATCH, DELETE | /products/{id} | detail, update approved fields, archive | MVP |
| POST | /products/{id}/stock | stock adjustment (stock_version) | MVP |
| GET | /jobs/{id} | status | MVP |
| GET | /jobs/{id}/events | SSE progress | MVP |

## C. Content and claim check
| Method | Path | Purpose | Class |
|---|---|---|---|
| POST | /posts/generate/{product_id} | generate a catalog-grounded draft | MVP |
| GET | /posts, /posts/{id} | list, detail with provenance | MVP |
| PATCH | /posts/{id} | edit draft | MVP |
| POST | /posts/{id}/claim-check | claim, verdict, evidence ids, severity, repair suggestion | MVP |
| POST | /posts/{id}/submit | submit for approval | MVP |
| POST | /posts/{id}/share-status | record per-channel status (manual) | STRETCH |
| GET | /posts/{id}/export | export approved content | STRETCH |

## D. Approvals
| Method | Path | Purpose | Class |
|---|---|---|---|
| GET | /approvals, /approvals/{id} | pending list; proposal, evidence, risk | MVP |
| POST | /approvals/{id}/approve | approve the specific proposal version | MVP |
| POST | /approvals/{id}/reject | reject | MVP |
| POST | /approvals/{id}/edit | edit then revalidate | MVP |

## E. Public store and chat (rate limited, authenticated customer accounts, store scoping)
| Method | Path | Purpose | Class |
|---|---|---|---|
| GET | /public/stores/{slug} | public store | MVP-next |
| POST | /public/customer-accounts/register, /login, /logout | customer account and session | MVP |
| GET | /public/customer-accounts/me | signed-in customer profile | MVP |
| POST | /public/stores/{slug}/sessions | authenticated customer chat | MVP-next |
| POST | /public/sessions/{id}/messages | authenticated customer message | MVP-next |
| GET | /public/sessions/{id}/stream | authenticated replies and escalation status | MVP-next |
| POST | /public/sessions/{id}/verify-phone/send, /verify | order-time OTP | FUTURE |
| POST | /public/sessions/{id}/order | order draft | MVP-next |
| GET | /widget.js | embeddable loader | STRETCH |

## F. Owner inbox and customers
| Method | Path | Class |
|---|---|---|
| GET | /conversations, /conversations/{id} | MVP-next |
| POST | /conversations/{id}/reply | MVP-next (owner-approved) |
| POST | /conversations/demo/start, /conversations/demo/simulate | dev/test only |
| GET | /businesses/me | MVP |
| POST | /conversations/{id}/block | STRETCH |
| GET | /customers/{id} | STRETCH (PII minimization) |

## G. Orders and payments
| Method | Path | Purpose | Class |
|---|---|---|---|
| GET | /orders, /orders/{id} | read | MVP-next |
| POST | /orders/{id}/confirm-payment | owner-confirmed record (never model-written) | MVP-next (simulated) |
| POST | /orders/{id}/remind, /ship | actions with state-machine checks | STRETCH |
| POST | /payments/link | payment provider | FUTURE |

## H. Trust and audit
| Method | Path | Class |
|---|---|---|
| GET | /audit-log, /guardrail/events | MVP |
| POST, GET | /reports, /disputes, /disputes/{id}/respond | FUTURE |

## I. Dashboard, channels, notifications
GET /dashboard (MVP). GET /channels (STRETCH). POST /channels/{type}/connect, /push/subscribe, GET /notifications (STRETCH/FUTURE). POST /webhooks/whatsapp, /instagram, /facebook: FUTURE, return 501 until a signed provider round-trip is tested.

## J. Observability and evaluation
GET /jobs/{id}/trace (MVP, sanitized, no raw reasoning). GET /evidence/{id} (MVP). GET, POST /evaluations/runs, GET /evaluations/runs/{id}, GET /metrics/agents?days=30 (STRETCH; tenant-scoped job/node latency, error counts, and recorded model-call metrics; unknown token/cost fields remain null).

## Cross-cutting
Error shape: problem JSON with request_id. Idempotency-Key header on order, approval and notification side effects. Pagination on list routes. All owner routes authorize role + business_id.
