# T-204: Post generation

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Generate mock/live-mode-labelled post drafts with explicit claims and deterministic price protection.
- **FILES:** `backend/app/routers/posts.py`, `backend/app/agents/nodes/{node_07_brief,node_08_draft}.py`, `backend/tests/unit/test_content_generation.py`
- **DEPENDS ON:** T-203
- **ACCEPTANCE:** Missing confirmed price returns 409; every fact claim records its product field; edits create a new draft revision; a hallucinated price rejects.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_content_generation.py -q`
- **SECURITY:** Only confirmed product context reaches generation; mock results are not quality claims.
- **OUT OF SCOPE:** Claim checking, submission and images.
- **STATUS:** Implemented with unit coverage.
