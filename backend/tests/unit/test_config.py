"""Unit tests for configuration validation outside dev."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_dev_settings_allowed() -> None:
    """Settings instantiate cleanly in dev mode with defaults."""
    s = Settings(ENV="dev")
    assert s.ENV == "dev"
    assert s.API_PREFIX == "/v1"


def test_production_settings_validation() -> None:
    """Non-dev environment raises ValueError if SECRET_KEY is default dev key or missing."""
    with pytest.raises(ValidationError):
        Settings(
            ENV="prod",
            SECRET_KEY="dev-secret-key-minimum-32-chars-long!",
            DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/db",
        )


def test_production_settings_success() -> None:
    """Non-dev environment passes when configured with valid non-dev secrets and db."""
    s = Settings(
        ENV="prod",
        SECRET_KEY="a-secure-production-random-secret-key-32-chars",
        DATABASE_URL="postgresql+psycopg://user:pass@prod-db.internal:5432/db",
    )
    assert s.ENV == "prod"
