# Backend tests

Backend tests use pytest and are split into fast unit tests and integration tests. Shared fixtures are in `conftest.py`.

## Use

From `backend/`:

```powershell
uv run pytest tests/unit -x -q
uv run pytest tests/integration -x -q
```

Unit tests should isolate network and database boundaries. Integration tests exercise configured service dependencies and API flows. Agent tests should cover tenant isolation, invalid model output, tool failures, injection attempts, retry limits, and approval enforcement.

## Metrics and impact

Test counts and pass rates are meaningful only when recorded from an actual run; this README makes no test-result claim. The suite's value is regression detection for API, data isolation, and agent controls.
