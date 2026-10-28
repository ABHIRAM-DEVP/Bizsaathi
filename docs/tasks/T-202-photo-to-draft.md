# T-202: Photo to product draft

- **PHASE:** 2  **PRIORITY:** P0
- **OBJECTIVE:** Create a product-draft proposal from 1–4 tenant-owned photos without writing catalogue facts.
- **FILES:** `backend/app/routers/products.py`, `backend/app/agents/nodes/node_04_extractor.py`, `backend/app/agents/nodes/node_06_reconciler.py`, `backend/tests/unit/test_photo_to_draft.py`
- **DEPENDS ON:** T-201
- **ACCEPTANCE:** Given valid photos, then 202 precedes work; blurry material is uncertain; duplicate names produce a conflict without changing products; cross-tenant media is 404; invalid output ends with a manual path.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_photo_to_draft.py -q`
- **SECURITY:** Upload ownership and idempotency are tenant-bound; output is suggestion-only.
- **OUT OF SCOPE:** Price/stock extraction, voice, live models.
- **STATUS:** Implemented with mock adapter coverage.
