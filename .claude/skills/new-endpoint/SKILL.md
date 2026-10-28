---
name: new-endpoint
description: Add a FastAPI route end to end (schema, repository, service with tenant authz, router, tests, OpenAPI export). Use when adding or changing an /v1 endpoint from docs/08-api-spec.md.
argument-hint: "[METHOD /v1/path - purpose]"
disable-model-invocation: true
---

# New endpoint: $ARGUMENTS

Prerequisite: task file with acceptance criteria and the route listed in docs/08-api-spec.md as MVP or STRETCH. FUTURE routes are not built.

Order:
1. Read .claude/rules/api.md, .claude/rules/db-tenancy.md, .claude/rules/security.md and one existing endpoint of similar shape.
2. Tests first: success, 422, 401, 403, 404, and a cross-tenant negative test (tenant B cannot touch tenant A). For long work: assert a job id is returned immediately. Show them fail.
3. Schemas, repository (tenant filter), service (authorization), router (response_model, status codes, tags, rate limit if public).
4. `just check-fast` until green. `just export-openapi`; regenerate the web client; confirm the contract diff is intended.
5. `just check` and `just smoke`. Run `security-reviewer` if auth, uploads or public routes changed.
6. Report with the AGENTS.md final report format.
