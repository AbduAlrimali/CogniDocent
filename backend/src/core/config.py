from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn, Field, model_validator
import logging

logger = logging.getLogger("app.core.config")


class AppSettings(BaseSettings):
    APP_NAME: str = "CogniDocent"
    LOGO_URL: str = Field(
        default="https://files.catbox.moe/00z6ji.png",
        validation_alias="LOGO_URL",
    )
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "CogniDocent is a powerful document search and retrieval tool that uses "
        "Large Language Models (LLMs) to provide accurate and relevant information "
        "from your documents."
    )
    APP_ROOT_PATH: str = "/api"
    APP_DOCS_PATH: str = "/"

    APP_ENV: str = Field(default="production", validation_alias="APP_ENV")
    APP_LOG_LEVEL: int = Field(default=logging.INFO, validation_alias="APP_LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Good practice: ignores extra env vars unrelated to this class
        frozen=True,
    )


class DatabaseSettings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cognidocent",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_db_settings() -> DatabaseSettings:
    return DatabaseSettings()
