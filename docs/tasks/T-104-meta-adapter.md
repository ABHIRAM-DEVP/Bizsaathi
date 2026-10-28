# TASK_ID: T-104
TITLE: Meta model adapter with mock and live clients, plus meta-smoke
PHASE: 1 (M2)
PRIORITY: MVP
OBJECTIVE: One adapter interface, a deterministic mock, and a live client that makes one verified call.
BACKGROUND: .claude/rules/meta-models.md, docs/12-assumptions-risks-deps.md (A-03, A-04, A-07), official Meta docs (human supplies URLs if blocked)
FILES TO CREATE OR MODIFY: app/ai/{interface,mock,live,smoke}.py, app/core/config.py, tests/unit/ai/test_adapter.py
IMPLEMENTATION STEPS:
  1. Read the official docs for base URL, auth, model ids, image input. If the docs cannot be reached, STOP and report; do not guess.
  2. Tests first on the mock: schema-valid output, schema-violating output raises, timeout, bounded retry on transient errors only, redaction.
  3. Implement interface + mock + live. IDs from config.
  4. Ask the human before running `just meta-smoke`. Record model id, date, usage in docs/12.
DEPENDS ON: T-102
ACCEPTANCE CRITERIA:
  - Given the mock, When a node calls generate_structured, Then a parsed model is returned.
  - Given malformed model text, When parsed, Then a typed error is raised (never best-effort text).
  - Given a missing key, When the live client starts, Then it fails with a clear config error and no secret in the message.
  - Given approval, When `just meta-smoke` runs, Then one real call succeeds and docs/12 records it (or the failure is reported honestly).
TEST COMMAND: just check-fast
SECURITY CONSIDERATIONS: key server-side only; no key in logs; PII redaction before sending.
OUT OF SCOPE: agent nodes, SAM, image generation
DEFINITION OF DONE: unit output quoted; live result recorded or marked NOT VERIFIED
