# 05 Troubleshooting runbook

Start with `/debug-fast`: reproduce, deepest error, one hypothesis, cheapest check.

## Symptom table
| Symptom | First check | Usual cause |
|---|---|---|
| Meta call 401/403 | `just meta-smoke` (ask first); check env var name loaded by config | missing/expired key, wrong base URL |
| Meta call 404 / model not found | compare configured ID with the verified ID in docs/12 | invented or unavailable model ID |
| Model returns text instead of schema | log raw (redacted) response; check parser | prompt/schema drift; treat as tool failure with bounded retry |
| Workflow loops | state retry counters; node events in /jobs/{id}/trace | missing retry cap or non-terminal edge |
| Job stuck "running" | worker logs; Redis connection | worker down, lost event |
| Approval approve fails | proposal version vs approval version | proposal edited after view; re-open |
| Cross-tenant test fails | repository query, missing business_id filter | forgot tenant filter in new repo method |
| 422 unexpected | request body vs schema in /docs | client out of sync; regenerate client |
| Web build type error after API change | `just export-openapi`, regenerate client | stale contract |
| PWA not installable | manifest, icons, HTTPS, service worker registration (devtools Application tab) | missing manifest fields, dev mode, no HTTPS |
| Offline shows stale or broken data | service worker cache rules | API JSON cached by mistake |
| "relation does not exist" | `uv run alembic current` | migration not applied |
| Eval numbers look great on first run | check split and mock/live label | mock mode, or tuned on heldout |
| Costs rising | model usage logs per node | repeated calls for deterministic work, no caching |
| Docker services down | `docker compose ps`, logs | `just up` not run, port in use |
| Windows path/line-ending issues in scripts | `file scripts/*.sh`; run via Git Bash/WSL | CRLF line endings |

## Agent-failure rules
Same check fails twice: `/debug-fast`. Three failures: write docs/tasks/<id>.stuck.md and stop. Polluted by patches: `git restore .` and re-run from the task file. Agent claims done: run `/verify-done` or `just check` yourself.

## Lessons log
| Date | Symptom | Root cause | Prevention |
|---|---|---|---|
