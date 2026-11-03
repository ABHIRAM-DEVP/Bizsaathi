# Evaluation dataset

This directory contains the evaluation case schema and labelled cases used by the repository's evaluation workflow.

## Architecture and use

Validate changes with `python scripts/eval_validate.py`. Keep cases synthetic or properly de-identified, preserve held-out splits, and do not tune against held-out results.

## Metrics and impact

The starter cases are test inputs, not evidence of model accuracy. Accuracy and safety claims require recorded runs against the appropriate labelled data and thresholds.
