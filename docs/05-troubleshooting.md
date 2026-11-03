# 05 Troubleshooting runbook

Start with `/debug-fast`: reproduce, deepest error, one hypothesis, cheapest check.

## Symptom table
| Symptom | First check | Usual cause |
|---|---|---|
| Meta call 401/403 | `just meta-smoke` (ask first); check env var name loaded by config | missing/expired key, wrong base URL |
| Meta call 404 / model not found | compare configured ID with the verified ID in docs/12 | invented or unavailable model ID |
| Model returns text instead of schema | log raw (redacted) response; check parser | prompt/schema drift; treat as tool failure with bounded retry |
| Post generation is slow or returns 502 | Check `POST /v1/posts/generate/{product_id}/stream` and stream logs for finish reason, output length, and JSON parse position (never raw copy) | Post generation has no model-response read timeout; connection, request-send, and connection-pool timeouts remain bounded. Complete lines can be recovered if only the final JSON closers were truncated. |
| Need a draft immediately while the AI provider is slow or unavailable | Choose **Quick local draft (no AI)** on the Posts page | Produces a clearly labelled local English, Hindi, or Marathi template; it is not AI-generated and must still be reviewed. |
| Workflow loops | state retry counters; node events in /jobs/{id}/trace | missing retry cap or non-terminal edge |
| Job stuck "running" | worker logs; Redis connection | worker down, lost event |
| Approval approve fails | proposal version vs approval version | proposal edited after view; re-open |
| Cross-tenant test fails | repository query, missing business_id filter | forgot tenant filter in new repo method |
| 422 unexpected | request body vs schema in /docs | client out of sync; regenerate client |
| Web build type error after API change | `just export-openapi`, regenerate client | stale contract |
| PWA not installable | manifest, icons, HTTPS, service worker registration (devtools Application tab) | missing manifest fields, dev mode, no HTTPS |
| Offline shows stale or broken data | service worker cache rules | API JSON cached by mistake |
| "relation does not exist" | `uv run alembic current` | migration not applied |
| "must be owner of table" during Docker startup | Check the table owner in PostgreSQL; set `MIGRATION_DATABASE_USER` to that role | `POSTGRES_USER` can connect but does not own the existing schema |
| Eval numbers look great on first run | check split and mock/live label | mock mode, or tuned on heldout |
| Costs rising | model usage logs per node | repeated calls for deterministic work, no caching |
| Docker services down | `docker compose ps`, logs | `just up` not run, port in use |
| Customer account signs in but chat does not open on localhost | Open the shared page and API using the same loopback hostname (`localhost` or `127.0.0.1`); customer chat and inbox requests normalize loopback API hosts to the page hostname | Cross-site cookie blocked when loopback hostnames differ |
| Windows path/line-ending issues in scripts | `file scripts/*.sh`; run via Git Bash/WSL | CRLF line endings |

For the ownership error, find the table owner with:

```sql
SELECT pg_get_userbyid(c.relowner) AS owner
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname = 'app_user';
```

Set `MIGRATION_DATABASE_USER` in the local `.env` to that owner's role. It defaults to `POSTGRES_USER`; `MIGRATION_DATABASE_PASSWORD` defaults to `POSTGRES_PASSWORD` and only needs setting if the owner uses a different password. These credentials are used only while Alembic runs; the API keeps using `POSTGRES_USER`. Do not delete the database volume to work around a permissions error.

## Agent-failure rules
Same check fails twice: `/debug-fast`. Three failures: write docs/tasks/<id>.stuck.md and stop. Polluted by patches: `git restore .` and re-run from the task file. Agent claims done: run `/verify-done` or `just check` yourself.

## Lessons log
| Date | Symptom | Root cause | Prevention |
|---|---|---|---|
