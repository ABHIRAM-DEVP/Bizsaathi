# TASK_ID: T-106
TITLE: Next.js shell with manifest, generated API client, six UI states
PHASE: 1
PRIORITY: MVP
OBJECTIVE: One Next.js app that builds, installs as a PWA candidate, and shows health-checked connection state.
BACKGROUND: docs/03-ui.md, .claude/rules/web-pwa.md, apps/web/CLAUDE.md (verify PWA requirements with current Next.js docs first)
FILES TO CREATE OR MODIFY: apps/web (scaffold), app/manifest.ts or public/manifest.json, app/layout.tsx, src/lib/api-client (generated), one test
IMPLEMENTATION STEPS:
  1. Check current official docs for Next.js PWA/manifest approach; record the source in the PR notes.
  2. Tests first: connection-state component renders loading, error, offline, success.
  3. Scaffold, manifest + icons, generated client from contracts/openapi.json.
DEPENDS ON: T-102
ACCEPTANCE CRITERIA:
  - Given the built app, When opened at 390px and 1280px, Then the same route renders without layout breakage (describe what was seen).
  - Given the API is down, When the shell loads, Then an honest error state shows.
  - Given the browser offline, When reloading, Then the shell or offline page shows; no tenant JSON is cached.
TEST COMMAND: just check
SECURITY CONSIDERATIONS: no secrets in NEXT_PUBLIC_*.
OUT OF SCOPE: feature pages, service-worker caching of API data
DEFINITION OF DONE: build output quoted; manifest validity checked or marked NOT VERIFIED
