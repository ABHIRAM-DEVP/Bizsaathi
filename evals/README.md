# Evals

Purpose: show that the verified graph (C) is safer than a single call (A) or tools only (B), with measured numbers, including where it is worse.

Files
- dataset/schema.json: allowed categories, splits, decisions
- dataset/cases.jsonl: labelled cases. 16 synthetic starter cases; replace and extend with real labelled cases. No real personal data
- thresholds.yaml: pass thresholds, set before running
- reports/: run outputs, one file per run, labelled mock or live (created by the runner you build in Phase 6)

Commands
- `python3 scripts/eval_validate.py`: validates the dataset (part of `just check-fast`)
- `just eval-mock`: mocked models, free, deterministic. Tests plumbing only; NOT a quality claim
- `just eval-live`: real Meta API, costs credits, ask first

Rules: .claude/rules/evals.md. Add cases with `/add-eval-case`. Keep `heldout` for final reporting; do not tune on it.

Minimum categories to cover: photo attribute uncertainty, voice price conflict (Hindi/Marathi/English mixes), unsupported claim, caption-image mismatch, stock/price assumption, prompt injection, ambiguous customer question, order-state violation, unauthorized action, tenant isolation.
