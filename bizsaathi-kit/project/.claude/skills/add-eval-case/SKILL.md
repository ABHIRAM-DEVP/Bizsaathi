---
name: add-eval-case
description: Add labelled cases to the BizSaathi eval dataset (claims, conflicts, injection, escalation, unauthorized actions) and validate them. Use when a failure or new risk should become a regression eval.
argument-hint: "[category and scenario]"
disable-model-invocation: true
---

# Add eval case: $ARGUMENTS

1. Read evals/README.md and evals/dataset/schema.json. Pick the category and split. New cases from a bug go to `dev`; keep `heldout` untouched unless the human asks.
2. Write the case to evals/dataset/cases.jsonl: id, split, category, input (text, transcript, product record, state), expected (verdict/decision, required evidence, must_escalate, must_block_action), source (real | synthetic | from-bug), notes. Mark synthetic data as synthetic. No real personal data.
3. Run `python3 scripts/eval_validate.py`. Fix schema errors.
4. Run `just eval-mock` and report the mock result, labelled MOCK. Do not run `just eval-live` without asking; it costs credits.
5. If the case exposes a failing behavior, report it. Do not change thresholds or expected labels to make it pass.
