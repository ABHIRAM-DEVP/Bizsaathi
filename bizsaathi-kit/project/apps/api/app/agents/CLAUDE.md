# apps/api/app/agents (LangGraph workflow nodes)

Read docs/07-agent-catalog.md and .claude/rules/agents.md before touching anything here.

- One node = one file = one typed input model, one typed output model, one permission set, one exit condition. Catalog entry first, code second.
- Not every node calls an LLM. Deterministic nodes (policy gate, reconciliation, permissions) must stay deterministic.
- State is a Pydantic model; reducers are explicit. Never put secrets or raw PII in state.
- Tools are typed functions with narrow permissions. No raw SQL tool, no payment-write tool, no publish tool inside the graph.
- Routing is conditional edges on typed results, with retry counters in state. Cap: 2 repairs, then `blocked` or `escalate`.
- Approval = LangGraph interrupt that stores a proposal version. Resume only with an owner approval bound to that version.
- Every node test: happy path, bad model output (schema violation), tool failure, injection string in input, retry-cap termination. Use the mock adapter; live tests are separate and opt-in.
- Emit observable events (tool, redacted I/O, evidence IDs, decision, retry, duration, error code). No chain-of-thought.
