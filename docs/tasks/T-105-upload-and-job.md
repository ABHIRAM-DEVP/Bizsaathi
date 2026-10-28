# TASK_ID: T-105
TITLE: Signed upload URL and async job record
PHASE: 1
PRIORITY: MVP
OBJECTIVE: A seller can upload a photo through a signed URL and a job record with status exists.
BACKGROUND: docs/08-api-spec.md (B), .claude/rules/security.md, apps/api/CLAUDE.md
FILES TO CREATE OR MODIFY: app/routers/uploads.py, app/services/uploads.py, app/routers/jobs.py, tests/integration/test_uploads.py
IMPLEMENTATION STEPS:
  1. Tests first for type, size, tenant-prefixed key, job creation.
  2. Implement POST /v1/uploads, GET /v1/jobs/{id}; MinIO via compose for dev.
DEPENDS ON: T-103
ACCEPTANCE CRITERIA:
  - Given an .exe renamed .jpg, When upload is requested or completed, Then rejected.
  - Given a valid jpeg under the size limit, When requested, Then a short-lived signed URL with a tenant-prefixed key is returned.
  - Given tenant B, When reading tenant A's job, Then 404.
TEST COMMAND: just check
SECURITY CONSIDERATIONS: allowlisted types, size caps, short-lived URLs.
OUT OF SCOPE: model calls, from-photo workflow
DEFINITION OF DONE: just check output quoted
