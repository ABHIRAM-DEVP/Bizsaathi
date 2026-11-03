# Core backend controls

`core/` holds cross-cutting infrastructure used by API and workflow code: application settings, database URL handling, development sessions, error formats, language/format helpers, structured logging, and tenant context.

## Architecture and use

Use centralized settings and shared helpers instead of local configuration or ad hoc request handling. Tenant identity and permissions must be enforced server-side for every protected data operation. Logs should contain observable events and request context, never secrets or raw chain-of-thought.

## Stack, metrics, and impact

Python, Pydantic Settings, and the shared database/logging libraries. No independent core-module metrics are recorded. These controls provide consistent configuration, tenant boundaries, and diagnosable API behavior across features.
