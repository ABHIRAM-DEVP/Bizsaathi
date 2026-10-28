---
name: new-agent-node
description: Add or change one LangGraph workflow node (typed input/output, tools, routing, tests, catalog entry). Use when implementing any of the 15 BizSaathi agent stages.
argument-hint: "[node number and name, e.g. 10 evidence-verifier]"
disable-model-invocation: true
---

# New agent node: $ARGUMENTS

Prerequisite: a task file in docs/tasks/ and the node's entry in docs/07-agent-catalog.md. If either is missing, stop and create it first.

Order:
1. Read .claude/rules/agents.md, apps/api/app/agents/CLAUDE.md and the catalog entry. Decide: LLM node or deterministic node? Use deterministic code unless interpretation is required.
2. Write tests first (mock adapter): happy path, schema-violating model output, tool failure, injection string in input, retry-cap termination, unauthorized action blocked. Show them fail.
3. Define Pydantic input and output models, the tool(s) with narrow permissions, and the node. Add conditional edges with retry counters; terminal states are `blocked` or `escalate`.
4. Emit observable events (tool, redacted I/O, evidence IDs, decision, retries, duration, error code).
5. Update the catalog entry if the contract changed. Run `just check-fast`, then `just check`.
6. If the node can affect customers, money or published content, run the `security-reviewer` subagent.
7. Report with the AGENTS.md final report format. State clearly that results use the mock adapter unless you ran live calls with approval.
