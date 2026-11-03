# Evaluations

Evaluations define repeatable checks of AI-assisted workflows and their safety boundaries. The intended comparison is A (single model call), B (tools/evidence), and C (full verified graph), including both improvements and regressions.

## Contents and architecture

- `dataset/schema.json`: allowed categories, splits, and decision fields.
- `dataset/cases.jsonl`: synthetic labelled cases; no real personal data.
- `thresholds.yaml`: pass targets and explicit `TODO` baselines.
- `reports/`: run output, labelled mock or live.

Cases exercise the implemented pipeline; thresholds must be set before a run and must not be weakened to get a pass. Keep held-out cases out of tuning. Follow `.claude/rules/evals.md`.

## Stack and commands

Python validation/evaluation scripts and the backend's model adapter; mock and live runs are separate. Dataset validation:

```powershell
python scripts/eval_validate.py
```

The repository runner includes validation in `python scripts/runner.py guards`. Run a live evaluation only when explicitly approved because it may use paid credits.

## Current metrics and impact

The current configured targets are `unauthorized_actions_blocked: 1.0`, `cross_tenant_leaks: 0`, and `duplicate_side_effects: 0`. `false_approval_rate`, `missed_escalation_rate`, `evidence_coverage`, claim precision/recall, extraction and cross-modal accuracy, p95 latency, and workflow cost are `TODO`. These values are targets, not measured outcomes.

The evaluation system's value is surfacing safety and quality regressions before relying on an agent workflow. No comparative A/B/C results or real-world impact metrics are claimed unless present in a dated report.
