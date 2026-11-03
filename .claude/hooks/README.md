# Agent hooks

> [Back to BizSaathi overview](../../README.md)

This directory contains shell hooks used by the local agent workflow, including path guards and a completion gate.

## Architecture and use

Hooks automate guardrails around edits and completion. They are developer tooling, not runtime API authorization; backend security controls and tests remain required. Shell prerequisites and execution behavior should be checked in each hook.

## Metrics and impact

No hook-block or false-positive rates are recorded. Their intended impact is catching disallowed edits and unverified completion claims earlier.
