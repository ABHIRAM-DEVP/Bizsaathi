# Evaluation Dataset

> Synthetic cases and thresholds for evaluating workflow safety and quality.

> [Back to BizSaathi overview](../../../README.md)

## What this folder contains

| Path | Purpose |
|---|---|
| `dataset/schema.json` | Allowed categories, dataset splits, and decision fields. |
| `dataset/cases.jsonl` | 16 synthetic starter cases; do not include real personal data. |
| `thresholds.yaml` | Pass targets. A `TODO` means a baseline is still required. |
| `reports/` | Per-run reports, labelled as mock or live. |

## Run the checks

```powershell
python scripts/eval_validate.py
just eval-mock
```

Mock evaluations verify deterministic plumbing only; they are not evidence of live-model quality. Live evaluations may incur provider costs and require explicit approval.

## Evaluation practice

Follow `.claude/rules/evals.md`. Keep held-out cases for final reporting; do not tune against them. Cover photo uncertainty, voice/price conflicts, unsupported claims, caption/image mismatch, stock/price assumptions, prompt injection, ambiguous customer questions, order-state violations, unauthorized actions, and tenant isolation.

Add cases with the `/add-eval-case` workflow. Set and justify thresholds before running evaluations; do not change them merely to make a run pass.
