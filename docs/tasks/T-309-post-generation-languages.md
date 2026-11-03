# T-309: Hindi and Marathi post generation

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Ensure post drafts honor the selected English, Hindi, or Marathi language in model-backed and mock workflows.
- **FILES:** `backend/app/services/post_generation.py`, `backend/app/agents/nodes/node_07_brief.py`, `backend/app/agents/nodes/node_08_draft.py`, `backend/app/ai/mock.py`
- **DEPENDS ON:** T-204
- **ACCEPTANCE:**
  - Hindi and Marathi codes are expanded to explicit language and script instructions in generation prompts.
  - The LangGraph brief and draft nodes preserve and apply the requested language.
  - Mock-mode post hooks are returned in the selected language; catalog facts remain server-sourced.
  - English behavior remains the default and is regression-tested.
- **TEST COMMAND:** `cd backend && uv run pytest tests/unit/test_post_generation_service.py tests/unit/test_content_generation.py -q`
- **SECURITY:** Keep confirmed catalog facts separate from generated copy; no external sends or paid model calls.
- **OUT OF SCOPE:** Translating catalog product names, prices, or other confirmed database facts.
- **STATUS:** Implemented; targeted backend unit tests passed.
