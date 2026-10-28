---
paths:
  - "evals/**"
  - "apps/api/app/evals/**"
---

# Evaluation rules
- Dataset in evals/dataset/cases.jsonl, schema in evals/dataset/schema.json. `scripts/eval_validate.py` must pass (part of check-fast).
- Split cases into `dev` (iterate against) and `heldout` (run for reported numbers only; do not tune prompts on it).
- Set pass thresholds BEFORE running. If a threshold cannot be justified yet, write TODO in evals/thresholds.yaml and run a baseline. Never invent a result.
- Three systems on the same cases: A (one Muse Spark call), B (Muse Spark + structured DB tools + evidence), C (full BizSaathi graph). Report quality, false approvals, missed escalations, latency, cost, including where C is worse.
- Metrics: field correctness, evidence coverage, claim-verification precision/recall, cross-modal mismatch accuracy, escalation quality, unauthorized actions blocked, workflow completion and duplicate side effects, p50/p95 latency, cost per workflow.
- Mock runs and live runs are separate commands and separate report files, labelled. Live runs record model id, date, usage.
- Failure cases are kept and published in the report, not removed.
