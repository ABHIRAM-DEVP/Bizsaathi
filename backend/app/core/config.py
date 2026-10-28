"""Application configuration using pydantic-settings."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: Literal["dev", "test", "staging", "prod"] = "dev"
    API_PREFIX: str = "/v1"
    PROJECT_NAME: str = "BizSaathi API"
    SECRET_KEY: str = "dev-secret-key-minimum-32-chars-long!"
    DATABASE_URL: str = "postgresql+psycopg://bizsaathi:bizsaathi@localhost:5432/bizsaathi"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_BUCKET: str = "bizsaathi-media"
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"

    # AI Model Provider settings (No paid API by default; mock or custom env provider)
    MODEL_PROVIDER: str = "mock"
    MODEL_API_KEY: str = ""
    MODEL_BASE_URL: str = ""

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENV not in ("dev", "test"):
            if not self.SECRET_KEY or "dev-secret" in self.SECRET_KEY:
                raise ValueError("SECRET_KEY must be securely configured outside dev/test environments")
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be configured for a production database outside dev/test")
        return self


settings = Settings()
