# T-203: Products, stock, minimal approvals

- **PHASE:** 2  **PRIORITY:** P0
- **OBJECTIVE:** Confirm seller-approved products through the execution boundary and safely manage stock.
- **FILES:** `backend/app/services/execution.py`, `backend/app/routers/{products,approvals}.py`, `backend/tests/unit/test_execution_and_approvals.py`
- **DEPENDS ON:** T-202
- **ACCEPTANCE:** Given absent confirmed price/stock, execution rejects; stale approvals and versions return 409; idempotent approvals execute once; negative and stale stock adjustments reject; tenant B receives 404.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_execution_and_approvals.py -q`
- **SECURITY:** Only execution writes confirmed facts; agents cannot import that service.
- **OUT OF SCOPE:** Orders and post approvals.
- **STATUS:** Implemented with unit coverage.
