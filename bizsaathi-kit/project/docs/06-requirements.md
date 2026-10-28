# 06 Requirements

Every requirement: unique ID, class (MVP/STRETCH/FUTURE), phase, Given/When/Then, verification. ASSUMPTION: classes and phases are proposals for you to confirm.

| ID | Requirement | Class | Phase | Acceptance (Given/When/Then) | Verification |
|---|---|---|---|---|---|
| REQ-001 | One Next.js app serves web and installable PWA | MVP | 1,4 | Given the built app, When opened on desktop and at 390px width, Then the same routes work; manifest valid | `just check`, Playwright |
| REQ-002 | Seller session auth with tenant scoping | MVP | 1 | Given tenant B's session, When requesting tenant A's product id, Then 404/403 | integration test |
| REQ-003 | Upload photo via signed URL | MVP | 1 | Given a 12MB .exe renamed .jpg, When uploading, Then rejected; valid jpeg accepted | upload tests |
| REQ-004 | Photo to product draft job returns job id immediately | MVP | 2 | Given a valid photo, When POST /products/from-photo, Then 202 + job id before model completes | API test |
| REQ-005 | Draft separates AI suggestions from confirmed facts | MVP | 2 | Given a draft, When rendered, Then each field shows Confirmed or Suggested | component test |
| REQ-006 | Conflicts are flagged, not silently resolved | MVP | 2 | Given spoken price != DB price, When reconciling, Then a conflict record is created and nothing overwritten | node test + ev-001 |
| REQ-007 | Content generation with evidence-linked claims | MVP | 2-3 | Given confirmed product facts, When generating a post, Then each factual claim has a verdict and evidence ids | node test |
| REQ-008 | Unsupported claims fail closed | MVP | 3 | Given an unverified claim, When submitting for approval, Then blocked or escalated | ev-003 |
| REQ-009 | Bounded repair | MVP | 3 | Given a failing check, When repair runs, Then at most 2 attempts then blocked | retry-cap test |
| REQ-010 | Independent verification controls | MVP | 3 | Given generated content, Then evidence verifier, critic and policy gate run as separate nodes | graph routing test |
| REQ-011 | Approval bound to proposal version | MVP | 3 | Given an approved proposal, When it is edited, Then approval invalid and checks re-run | approval test |
| REQ-012 | Audit trail of decisions and actions | MVP | 3 | Given any approval or block, Then an audit event exists | integration test |
| REQ-013 | Agents cannot write payment status or publish | MVP | 3 | Given an agent path, When attempting payment write, Then denied | ev-010 + unit |
| REQ-014 | Model access via adapter; keys server-side | MVP | 1 | Given built frontend, When scanning bundle, Then no key; mock and live adapters selectable | secret scan + test |
| REQ-015 | Verified Meta call recorded | MVP | 1 | Given credentials, When `just meta-smoke`, Then model id/date/usage recorded in docs/12 | manual evidence |
| REQ-016 | Public chat answers only from verified records | MVP-next | 4 | Given a stock question, When tool returns stock, Then answer cites evidence; else escalate | ev-005, ev-008 |
| REQ-017 | Prompt-injection resistance | MVP | 3-4 | Given instruction-like text in customer or transcript input, Then permissions and policy unchanged | ev-006, ev-007 |
| REQ-018 | Order state machine | MVP-next | 4 | Given AWAITING_PAYMENT, When ship requested, Then blocked | ev-009 |
| REQ-019 | Evals: dataset, A/B/C comparison, thresholds | MVP | 5 | Given heldout split, When live run, Then report with metrics and failures | `just eval-live` (approved) |
| REQ-020 | Voice note to fields | STRETCH | 2 | Given a Hindi/Marathi/English note, When transcribed, Then fields extracted with transcript spans | tests + real samples |
| REQ-021 | SAM 3.1 segmentation | STRETCH | 2 | Given a photo, When segmenting, Then mask returned and labelled non-verifying | test; only if access verified |
| REQ-022 | PWA offline behavior | MVP | 4 | Given offline, When opening app, Then shell + honest offline message; no cached tenant JSON | Playwright |
| REQ-023 | Social channel webhooks | FUTURE | - | not built; routes return 501 | - |
| REQ-024 | Real payments, KYC | FUTURE | - | not built; labelled simulated | - |

## Non-functional
Security (rules in .claude/rules/security.md); reliability (timeouts, bounded retries, idempotency); performance (record p50/p95, no invented targets: TODO baseline); accessibility (WCAG-minded checks, TODO tool); observability (OpenTelemetry spans, observable events); maintainability (one command set, ADRs).
