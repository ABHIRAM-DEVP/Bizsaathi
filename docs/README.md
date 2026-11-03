# Project documentation

> [Back to BizSaathi overview](../README.md)

This folder is the human-readable source for BizSaathi's product intent, architecture, requirements, data model, endpoint behavior, agent controls, testing, risks, and demo guidance.

## How to navigate

- `00-vision.md` and `06-requirements.md`: product goals and requirements.
- `01-architecture.md`, `07-agent-catalog.md`: system and workflow design.
- `08-api-spec.md`, `14-endpoint-specs.md`, `15-schema-and-formats.md`: API and data contracts.
- `04-test-strategy.md`, `05-troubleshooting.md`: verification and operations.
- `adr/`: accepted architectural decisions.
- `tasks/`: implementation tasks and acceptance criteria.
- `schema/`: reference DDL; it is not an applied migration.
- `source/`: source material, not the current implementation contract.
- `prompts/`: workflow prompts and runbooks.
- `status/`: dated or task-specific status notes.

## Metrics and impact

The evaluation thresholds and run results live in [../evals/](../evals/README.md). Architecture and requirement documents describe intended safeguards and product value, not measured production outcomes. Mark unknowns explicitly and update decisions through an ADR.
