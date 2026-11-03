"""Unit tests for environment-backed configuration."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

TEST_SETTINGS = {
    "ENV": "dev",
    "PROJECT_NAME": "Test API",
    "SECRET_KEY": "test-only-secret-placeholder",
    "DATABASE_URL": "postgresql+psycopg://test@db.example.test/test_db",
    "REDIS_URL": "redis://cache.example.test/0",
    "CORS_ALLOWED_ORIGINS": "https://web.example.test",
    "DEV_BUSINESS_NAME": "Test Shop",
    "DEV_BUSINESS_SLUG": "test-shop",
    "LOW_STOCK_THRESHOLD": 5,
    "STORAGE_BUCKET": "test-bucket",
    "STORAGE_ENDPOINT": "https://storage.example.test",
    "STORAGE_REGION": "test-region-1",
    "MEDIA_STORAGE_PATH": "test-media",
    "SIGNED_URL_TTL_SECONDS": 900,
    "STORAGE_ACCESS_KEY": "test-access-placeholder",
    "STORAGE_SECRET_KEY": "test-secret-placeholder",
    "MODEL_MOCK_MODE": True,
    "MODEL_API_KEY": "",
    "MODEL_BASE_URL": "https://models.example.test/v1",
    "MODEL_ID": "test-model",
    "MODEL_REQUEST_TIMEOUT_SECONDS": 30,
    "MODEL_MAX_RETRIES": 2,
}


def test_dev_settings_require_explicit_environment_values() -> None:
    settings = Settings.model_validate(TEST_SETTINGS)

    assert settings.ENV == "dev"
    assert settings.API_PREFIX == "/v1"
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_production_settings_validation() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                **TEST_SETTINGS,
                "ENV": "prod",
                "SECRET_KEY": "",
                "DATABASE_URL": "postgresql+psycopg://test@localhost/test_db",
            },
        )


def test_production_settings_success() -> None:
    settings = Settings.model_validate(
        {
            **TEST_SETTINGS,
            "ENV": "prod",
            "SECRET_KEY": "non-development-test-key-placeholder",
        },
    )
    assert settings.ENV == "prod"


def test_app_env_names_enable_configured_live_reasoning() -> None:
    settings = Settings.model_validate(
        {
            **{
                key: value
                for key, value in TEST_SETTINGS.items()
                if key not in {"ENV", "MODEL_API_KEY", "MODEL_BASE_URL", "MODEL_ID"}
            },
            "APP_ENV": "development",
            "REASONING_API_KEY": "test-key-placeholder",
            "MODEL_API_BASE_URL": "https://models.example.test/v1",
            "REASONING_MODEL": "test-model",
            "MODEL_MOCK_MODE": False,
        },
    )

    assert settings.ENV == "dev"
    assert settings.MODEL_PROVIDER == "live"
    assert settings.MODEL_API_KEY.get_secret_value() == "test-key-placeholder"
    assert settings.MODEL_BASE_URL == "https://models.example.test/v1"
    assert settings.MODEL_ID == "test-model"


def test_explicit_mock_mode_does_not_select_live_provider() -> None:
    settings = Settings.model_validate(
        {
            **{
                key: value
                for key, value in TEST_SETTINGS.items()
                if key not in {"MODEL_API_KEY", "MODEL_BASE_URL", "MODEL_ID"}
            },
            "REASONING_API_KEY": "test-key-placeholder",
            "MODEL_API_BASE_URL": "https://models.example.test/v1",
            "REASONING_MODEL": "test-model",
            "MODEL_MOCK_MODE": True,
        },
    )

    assert settings.MODEL_PROVIDER == "mock"


def test_mock_flag_takes_precedence_over_live_provider_setting() -> None:
    settings = Settings.model_validate(
        {
            **TEST_SETTINGS,
            "MODEL_PROVIDER": "live",
            "MODEL_MOCK_MODE": True,
        },
    )

    assert settings.MODEL_PROVIDER == "mock"


def test_settings_redacts_model_api_key_from_repr() -> None:
    settings = Settings.model_validate(
        {
            **{key: value for key, value in TEST_SETTINGS.items() if key != "MODEL_API_KEY"},
            "REASONING_API_KEY": "test-key-placeholder",
        },
    )
    assert "test-key-placeholder" not in repr(settings)
    assert settings.MODEL_API_KEY.get_secret_value() == "test-key-placeholder"


def test_jwt_secret_environment_alias_is_loaded() -> None:
    settings = Settings.model_validate(
        {
            **{key: value for key, value in TEST_SETTINGS.items() if key != "SECRET_KEY"},
            "JWT_SECRET": "jwt-env-test-placeholder",
        },
    )

    assert settings.SECRET_KEY.get_secret_value() == "jwt-env-test-placeholder"
