# T-201: Graph foundation

- **PHASE:** 2  **PRIORITY:** P0
- **OBJECTIVE:** Provide typed LangGraph job execution with bounded budgets, checkpoint references, observable trace events, model usage and tenant-scoped read tools.
- **FILES:** `backend/app/agents/`, `backend/tests/unit/test_agent_graph.py`, `docs/15-schema-and-formats.md`
- **DEPENDS ON:** T-105
- **ACCEPTANCE:** Given a job run, then events are ordered and omit reasoning; given budget 2 and 3 calls, then it blocks; given business A, read tools never return B.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_agent_graph.py -q`
- **SECURITY:** State supplies `business_id`; tools are read-only.
- **OUT OF SCOPE:** Model-calling nodes and approvals.
- **STATUS:** Implemented; backend unit coverage exists.
