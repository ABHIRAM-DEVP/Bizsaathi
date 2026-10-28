# 12 Assumptions, risks, dependencies, verified findings

Never convert an assumption into a requirement or fact silently. Update status when evidence arrives.

## Assumptions register
| ID | Assumption | Why it matters | Evidence now | Risk if wrong | Validation | Owner | Status |
|---|---|---|---|---|---|---|---|
| A-01 | Hackathon deadline is early November (plan: Nov 4) | schedule | 2.0 plan only | missed submission | read official event guide | you | OPEN |
| A-02 | No paid Meta API models used; free/env-configured keys only | budget & policy | User explicit constraint | unexpected cost | env inspection | user | VERIFIED (Zero Paid API) |
| A-03 | Reasoning model id is mock/configurable | adapter config | User policy | 404s | mock adapter; env config | you | RESOLVED (Mock/Env) |
| A-04 | Image analysis handled by mock/env-configured adapter | photo flow | User policy | redesign intake | mock adapter fixtures | you | RESOLVED (Mock/Env) |
| A-05 | Transcribe model handled by mock/env-configured adapter | voice stretch | User policy | drop voice | mock adapter fixtures | you | RESOLVED (Mock/Env) |
| A-06 | SAM segmentation handled by mock/env-configured adapter | segmentation stretch | User policy | drop SAM | mock adapter fixtures | you | RESOLVED (Mock/Env) |
| A-07 | Model adapter follows standard unified interface | adapter simplicity | internal contract | custom client | app/ai/interface.py | you | RESOLVED |
| A-08 | Team size is 1 (solo) | scope | 2.0 plan implies solo; brief says TODO | overcommit | confirm | you | OPEN |
| A-09 | Python 3.12 and Node LTS available on your Windows machine | tooling | Verified (Python 3.12.7, Node v24.22.1) | env churn | verified via terminal | you | VERIFIED |
| A-10 | Mock OTP is acceptable for the demo | auth scope | brief excludes real KYC | judge expectation | confirm | you | OPEN |

## Verified findings (fill from official sources; cite URL and date)
| Item | Finding | Source URL | Date | Verified by |
|---|---|---|---|---|
| Python version | Python 3.12.7 installed | Windows terminal | 2026-10-28 | Agent |
| Node.js version | Node.js v24.22.1, npm 11.6.4 installed | Windows terminal | 2026-10-28 | Agent |
| uv version | uv 0.12.23 installed | Windows terminal | 2026-10-28 | Agent |
| Docker version | Docker 29.7.2 installed | Windows terminal | 2026-10-28 | Agent |
| jq version | jq 1.6 installed | Windows terminal | 2026-10-28 | Agent |
| just status | MISSING | Windows terminal | 2026-10-28 | Agent (fallback: python runner) |
| pnpm status | MISSING | Windows terminal | 2026-10-28 | Agent (fallback: npm) |
| mmdc status | MISSING | Windows terminal | 2026-10-28 | Agent (diagrams unverified) |

## Risk register
| Risk | Mitigation | Owner |
|---|---|---|
| Paid API charges | Mock adapter default; strict env-only API keys; no paid Meta models | all |
| Hallucinated product facts | DB-backed facts, schemas, evidence checks, seller confirmation | agents |
| Unsupported marketing claims | verifier, bounded repair, approval | agents |
| Cross-tenant leakage | server-side tenancy, negative tests, maybe RLS | api |
| API key leakage | server-only env, secret scan, hook, redaction | all |
| Latency/cost overrun | usage logs, caps, async jobs, safe caching | api |
| PWA offline confusion | cache shell only, honest states | web |
| Scope creep | MVP/STRETCH/FUTURE, feature freeze 1 day before deadline | you |
| Broken deployment | health checks, migrations, tested fallback (local demo) | you |
| Agent claims false completion | runner guards, /verify-done, verification evidence | process |

## Dependency register
| Dependency | Needed for | Owner | Status | Version | Fallback |
|---|---|---|---|---|---|
| Model API key | live AI | you | OPTIONAL (.env) | - | mock adapter for dev/evals |
| Python, uv | API | you | VERIFIED | Python 3.12.7, uv 0.12.23 | - |
| Node, npm | web | you | VERIFIED | Node v24.22.1, npm 11.6.4 | pnpm missing, using npm |
| Docker Desktop | Postgres/Redis/MinIO | you | VERIFIED | Docker 29.7.2 | local installs |
| PostgreSQL (+pgvector optional) | data | compose | READY | - | local install |
| Redis | jobs/cache (when justified) | compose | READY | - | in-process jobs |
| S3-compatible storage | media | MinIO | READY | - | local disk (dev only) |
| Hosting for demo | public URL | you | TODO | - | local demo + video |
| Official docs access | verification | you | READY | - | - |
| Task runner (just) | automation | you | MISSING | - | python scripts/runner.py |
