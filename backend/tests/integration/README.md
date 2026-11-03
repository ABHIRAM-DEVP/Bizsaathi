# Backend integration tests

> [Back to BizSaathi overview](../../../README.md)

This folder contains tests that exercise connected API and persistence behavior across backend components.

## Use

Run from `backend/` with `uv run pytest tests/integration -x -q`. Follow the configured local dependency setup and keep tenant-isolation and authorization negatives in coverage.

## Metrics and impact

No aggregate integration pass rate is asserted by this README. These tests check that components work together with the configured services; they are not production availability measurements.
