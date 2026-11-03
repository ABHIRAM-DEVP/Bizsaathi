"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    ENV: Literal["dev", "test", "staging", "prod"] = Field(validation_alias=AliasChoices("ENV", "APP_ENV"))
    API_PREFIX: str = "/v1"
    PROJECT_NAME: str = Field(validation_alias=AliasChoices("PROJECT_NAME", "APP_NAME"))
    SECRET_KEY: SecretStr = Field(validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"))
    DATABASE_URL: str
    REDIS_URL: str
    CORS_ALLOWED_ORIGINS: str
    DEV_BUSINESS_NAME: str = Field(min_length=1, max_length=120)
    DEV_BUSINESS_SLUG: str = Field(min_length=1, max_length=63)
    LOW_STOCK_THRESHOLD: int = Field(ge=0)
    STORAGE_BUCKET: str = Field(validation_alias=AliasChoices("STORAGE_BUCKET", "OBJECT_STORAGE_BUCKET", "S3_BUCKET"))
    STORAGE_ENDPOINT: str = Field(
        validation_alias=AliasChoices("STORAGE_ENDPOINT", "OBJECT_STORAGE_ENDPOINT", "S3_ENDPOINT_URL")
    )
    STORAGE_REGION: str = Field(validation_alias=AliasChoices("STORAGE_REGION", "OBJECT_STORAGE_REGION"))
    MEDIA_STORAGE_PATH: str
    SIGNED_URL_TTL_SECONDS: int = Field(gt=0, le=604800)
    STORAGE_ACCESS_KEY: SecretStr = Field(
        validation_alias=AliasChoices("STORAGE_ACCESS_KEY", "OBJECT_STORAGE_ACCESS_KEY", "S3_ACCESS_KEY")
    )
    STORAGE_SECRET_KEY: SecretStr = Field(
        validation_alias=AliasChoices("STORAGE_SECRET_KEY", "OBJECT_STORAGE_SECRET_KEY", "S3_SECRET_KEY")
    )

    MODEL_PROVIDER: Literal["mock", "live", "openai", "generic"] | None = None
    MODEL_MOCK_MODE: bool
    MODEL_API_KEY: SecretStr = Field(validation_alias=AliasChoices("MODEL_API_KEY", "REASONING_API_KEY"))
    MODEL_BASE_URL: str = Field(validation_alias=AliasChoices("MODEL_BASE_URL", "MODEL_API_BASE_URL"))
    MODEL_ID: str = Field(validation_alias=AliasChoices("MODEL_ID", "REASONING_MODEL"))
    MODEL_REQUEST_TIMEOUT_SECONDS: float = Field(gt=0, le=120)
    MODEL_MAX_RETRIES: int = Field(ge=0, le=2)

    @field_validator("ENV", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return {"development": "dev", "production": "prod"}.get(value.lower(), value.lower())

    @model_validator(mode="after")
    def apply_provider_mode_and_validate_secrets(self) -> "Settings":
        if self.MODEL_MOCK_MODE:
            self.MODEL_PROVIDER = "mock"
        elif self.MODEL_PROVIDER is None:
            self.MODEL_PROVIDER = "live"

        if self.ENV not in ("dev", "test"):
            secret = self.SECRET_KEY.get_secret_value()
            if not secret or "dev-secret" in secret:
                raise ValueError("SECRET_KEY must be securely configured outside dev/test environments")
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be configured for a production database outside dev/test")
        return self


settings = Settings()  # type: ignore[call-arg]
