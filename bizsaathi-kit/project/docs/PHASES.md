# Phases

ASSUMPTION: the dates below come from the BizSaathi 2.0 plan (Oct 27 to Nov 4). The real deadline and time zone are TODO until read from the official event guide. Freeze features at least 1 day before it.

Rule: one task file per slice, each independently shippable, each ending with `just check` green and a commit. Never start a phase on a red check.

| # | Phase | Planned dates | Output you can run | Gate (evidence required) |
|---|---|---|---|---|
| 0 | Repo + environment verified | Oct 27-28 | tools installed, `just guards` green, kit installed | M0 |
| 1 | Foundations | Oct 27-28 | FastAPI + Postgres + migrations, Meta adapter + `meta-smoke`, upload flow, job table, nodes 01-03 skeleton, web shell + manifest | `just check`, one real Meta call recorded |
| 2 | Multimodal intelligence | Oct 29-30 | photo-to-draft with uncertainty flags, catalogue reconciliation, content generation; STRETCH: voice, SAM | conflict (price/colour) flagged in a test |
| 3 | Verification | Oct 31-Nov 1 | evidence refs, verifier, critic, policy gate, bounded repair, approvals, audit | claim cases pass in `eval-mock`; approval interrupt test |
| 4 | Customer + order | Nov 2 | public chat grounded answers, escalation, order draft (payment simulated) | escalation case + order state tests |
| 5 | Evals + submission | Nov 3-4 | live eval A/B/C run, deployment, README, demo video | scorecard with real numbers; deployed URL verified |

## Milestones with exit criteria
- M0: repo audited; `just guards` green; tool versions recorded.
- M1: docs 00-03, 06-08 reviewed by you; assumptions answered or accepted; Phase 1 tasks approved.
- M2: backend + DB + one verified Meta call (model id, date recorded in docs/12).
- M3: end-to-end product workflow (photo -> draft -> seller confirm) with tests.
- M4: web/PWA interface working at mobile and desktop width.
- M5: verifier, critic, policy gate, repair cap, approval and audit tested.
- M6: customer workflow and chosen stretch items.
- M7: eval report, deployment, demo validated.

## Deferred (outside the critical path)
Social webhooks, real SMS OTP, KYC, fine-tuning, open-weight GPU deployment, knowledge graphs, multi-model debate.

## Task board
| Task | Phase | Status | Commit |
|---|---|---|---|
| T-101..T-106 | 1 | seeded in docs/tasks/ | |
