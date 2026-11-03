# T-204: Post generation

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Generate mock/live-mode-labelled three-line post drafts grounded in seller-saved product descriptions and attributes, with explicit claims and deterministic price protection, plus an immediate local-template option when AI latency is unacceptable.
- **FILES:** `backend/app/routers/posts.py`, `backend/app/agents/nodes/{node_07_brief,node_08_draft}.py`, `backend/tests/unit/test_content_generation.py`
- **DEPENDS ON:** T-203
- **ACCEPTANCE:** Missing confirmed price returns 409; every generated draft has two editable creative lines followed by a server-composed verified product-and-price line; live-generation prompts include seller-saved descriptions and attributes as untrusted data and instruct the model to use only explicitly stated features; creative claims remain unverified and carry source evidence IDs when details are provided; edits create a new draft revision; a hallucinated price rejects; live generation streams with a 10-second connect timeout, no read timeout, at most 2,048 output tokens, and no retry; the explicit local-template endpoint returns an English, Hindi, or Marathi draft without a model call and labels it `mock`.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_content_generation.py tests/unit/test_post_generation_service.py tests/unit/test_ai_adapter.py -q`
- **SECURITY:** Only confirmed product context reaches generation; mock results are not quality claims.
- **OUT OF SCOPE:** Claim checking, submission and images.
- **STATUS:** Implemented with unit coverage.
