# Repository agent configuration

This folder contains repository-scoped instructions and automation for coding agents. It complements `AGENTS.md` and `CLAUDE.md`; it is not part of the deployed application.

## Contents

- `agents/`: specialized read-only or implementation agent instructions.
- `hooks/`: path/safety guards and a completion gate.
- `rules/`: scoped API, database/tenancy, model, testing, security, and web rules.
- `skills/`: repeatable workflows for creating endpoints, pages, migrations, agent nodes, and eval cases.
- `settings.json`: repository agent settings.

## Metrics and impact

This configuration has no runtime product or business metrics. Its intended value is consistent reviews, safer edits, and repeatable engineering workflows; those outcomes are not quantitatively measured here.
