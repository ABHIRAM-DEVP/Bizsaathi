"""Keep the test suite isolated from any developer-configured live model."""

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def use_deterministic_mock_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent unit and integration tests from making external model calls."""
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "mock")
