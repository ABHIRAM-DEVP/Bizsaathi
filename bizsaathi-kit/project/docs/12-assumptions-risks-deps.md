# 12 Assumptions, risks, dependencies, verified findings

Never convert an assumption into a requirement or fact silently. Update status when evidence arrives.

## Assumptions register
| ID | Assumption | Why it matters | Evidence now | Risk if wrong | Validation | Owner | Status |
|---|---|---|---|---|---|---|---|
| A-01 | Hackathon deadline is early November (plan: Nov 4) | schedule | 2.0 plan only | missed submission | read official event guide | you | OPEN |
| A-02 | $150 Meta API credits are available to this account | budget | brief says previously supplied | no live evals | check account dashboard | you | OPEN |
| A-03 | Reasoning model id is `muse-spark-1.3` | adapter config | 2.0 plan says "subject to availability"; searches mention Muse Spark 1.1 | 404s | `just meta-smoke`; official docs | you | OPEN |
| A-04 | Muse Spark accepts image input via the API | photo flow | Meta pages describe multimodal models | redesign intake | live test | you | OPEN |
| A-05 | Muse Voice Transcribe is API-accessible and handles Hindi/Marathi | voice stretch | Meta Connect listing only | drop voice | live test with real samples | you | OPEN |
| A-06 | SAM 3.1 is accessible to this account | segmentation stretch | 2.0 plan | drop SAM | official docs/access | you | OPEN |
| A-07 | Meta REST API works with OpenAI/Anthropic-style client SDKs | adapter simplicity | freeCodeCamp course description only | write custom client | read official API docs | you | OPEN |
| A-08 | Team size is 1 (solo) | scope | 2.0 plan implies solo; brief says TODO | overcommit | confirm | you | OPEN |
| A-09 | Python 3.12 and Node LTS available on your Windows machine | tooling | unverified | env churn | `python --version`, `node -v` | you | OPEN |
| A-10 | Mock OTP is acceptable for the demo | auth scope | brief excludes real KYC | judge expectation | confirm | you | OPEN |

## Verified findings (fill from official sources; cite URL and date)
| Item | Finding | Source URL | Date | Verified by |
|---|---|---|---|---|
| Meta base URL and auth | | | | |
| Reasoning model id | | | | |
| Image input format/limits | | | | |
| Transcribe model id, languages | | | | |
| SAM 3.1 access | | | | |
| Rate limits and pricing | | | | |

Note from kit creation: dev.meta.ai pages could not be fetched in the kit-building environment (not on its allowlist), so nothing about Meta API specifics was verified here.

## Risk register
| Risk | Mitigation | Owner |
|---|---|---|
| Meta API/model unavailable | adapter + labelled mock; verify access day 1 | you |
| Hallucinated product facts | DB-backed facts, schemas, evidence checks, seller confirmation | agents |
| Unsupported marketing claims | verifier, bounded repair, approval | agents |
| Cross-tenant leakage | server-side tenancy, negative tests, maybe RLS | api |
| API key leakage | server-only env, secret scan, hook, redaction | all |
| Latency/cost overrun | usage logs, caps, async jobs, safe caching | api |
| PWA offline confusion | cache shell only, honest states | web |
| Scope creep | MVP/STRETCH/FUTURE, feature freeze 1 day before deadline | you |
| Broken deployment | health checks, migrations, tested fallback (local demo) | you |
| Agent claims false completion | Stop hook, /verify-done, `just check` evidence | process |

## Dependency register
| Dependency | Needed for | Owner | Status | Version | Fallback |
|---|---|---|---|---|---|
| Meta API key + credits | all live AI | you | TODO | - | mock adapter for dev |
| Python, uv | API | you | TODO verify | | |
| Node, pnpm | web | you | TODO verify | | |
| Docker Desktop | Postgres/Redis/MinIO | you | TODO verify | | local installs |
| PostgreSQL (+pgvector optional) | data | compose | | | |
| Redis | jobs/cache (when justified) | compose | | | in-process jobs |
| S3-compatible storage | media | MinIO | | | local disk (dev only) |
| Hosting for demo | public URL | you | TODO | | local demo + video |
| Official docs access | verification | you | | | |
