# ADR-0003: LangGraph as Typed Agent Runtime

- Status: accepted
- Date: 2026-10-28

## Context
Phase 2 (and the AGENTS.md contract) specifies LangGraph for agent orchestration with typed state, checkpointing, and approval interrupts.

## Decision
Adopt `langgraph>=1.2.0` (with `langchain-core` and `langgraph-checkpoint`) as the workflow execution engine for multi-node agent pipelines.

## Consequences
- Agents run as deterministic stategraphs with explicit node definitions and typed state schemas.
- Checkpoints allow persistence and resumption of workflows across seller approval interrupts.
- All state updates remain typed and validated with Pydantic schemas.
