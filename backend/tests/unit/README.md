# Backend unit tests

> [Back to BizSaathi overview](../../../README.md)

This folder contains fast pytest tests for backend modules and behavior that can be checked without integration services.

## Use

Run from `backend/` with `uv run pytest tests/unit -x -q`. Isolate model calls at the adapter boundary and avoid network or real database dependencies.

## Metrics and impact

Report test results only from an actual run. Unit tests help detect local logic regressions quickly but do not replace integration or live-model evaluation.
