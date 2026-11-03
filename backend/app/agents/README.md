# Agent workflows

This package implements the LangGraph workflows and their typed state, nodes, and tools. Workflows coordinate seller product/content tasks and the grounded customer-response path; they are not a source of confirmed prices, stock, or policy facts.

## Architecture and use

Inputs are normalized into workflow state, tools retrieve tenant-scoped facts, and model-backed nodes produce constrained proposals. Independent evidence and policy controls validate output. Repairs are bounded; unsupported or unsafe work stops or escalates. Actions with side effects require owner approval and are executed outside the model.

Use this package when changing graph topology, state, node behavior, or agent tool permissions. Keep model integration behind `app/ai/` and cover failure, tenant, injection, and approval paths with tests.

## Stack, metrics, and impact

Python, LangGraph, typed Pydantic/domain models, and pytest. Evaluation targets live in `evals/thresholds.yaml`; most quality values are still `TODO`, and no production quality or latency result is asserted here. The intended impact is useful automation with reviewable evidence and bounded risk, not autonomous decision-making.
