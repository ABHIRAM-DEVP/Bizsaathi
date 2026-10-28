---
name: debug-fast
description: Use when a command, test or app fails and the cause is not obvious, or after the same fix has already failed once. Fixed protocol - reproduce, read the deepest error, one hypothesis at a time, fix with a regression test.
---

# Debug protocol

Do not edit code until step 3 is done.

1. Reproduce: find the smallest command that fails (one test, one curl, one page). Paste its exact output.
2. Read the deepest error: the last exception or "Caused by", and the first frame inside our own code. Ignore the frame noise in between. Fix the first error only, because later ones often cascade.
3. Classify the failure: environment/config, dependency/version, type or contract mismatch, data/state, logic, timing/concurrency, network/infra.
4. One hypothesis at a time. Test the cheapest check first (a log line, a single test, curl, a psql query). Write: hypothesis -> check -> result.
5. Minimal fix, plus a regression test that failed before the fix and passes after.
6. "It used to work": compare with the last green commit (git diff, git bisect). Clean builds and fresh containers expose stale artifacts.
7. Record a 1-3 line lesson in docs/05-troubleshooting.md if the cause was surprising.

## Cheapest first checks by layer
- API: `uv run pytest -x -q --lf`, `curl -i <url>`, `docker compose logs --tail=100 api`
- Web: `pnpm typecheck`, browser console, network tab response body
- Database: `psql`, `EXPLAIN (ANALYZE, BUFFERS) <query>`, `alembic current`
- Redis: `redis-cli --scan --pattern 'prefix:*' | head`, `redis-cli TTL <key>`
- Containers: `docker compose ps`, then logs of the failing service

If two hypotheses fail, stop and write docs/tasks/<slug>.stuck.md instead of trying a third guess.
