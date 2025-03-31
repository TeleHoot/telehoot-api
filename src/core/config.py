from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings, utils


@utils.Singleton
class Settings(BaseSettings):
    APP_TITLE: str = "TeleHootAPI"
    APP_DESCRIPTION: str = "API for TeleHoot"
    APP_VERSION: str = "0.1.0"

    DOCS_URL: str | None = "/docs"
    REDOC_URL: str | None = "/redoc"

    DEBUG: bool = False

    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_EXPIRE_TIME: int = 86400 * 7  # 7 дней

    DOMAIN: str = "example.site"

    ALLOW_ORIGINS: list[str] = ["*"]
    ALLOW_HOSTS: list[str] = ["*"]

    POSTGRES: settings.PostgreSQLSettings = settings.PostgreSQLSettings()

    API_PREFIX: str = "/api"

    TOKEN_PREFIX: str = "TOKEN"
    USER_ROLE: str = "USER"
    ADMIN_ROLE: str = "ADMIN"

    model_config = SettingsConfigDict(env_file=Path(__file__).parents[2] / ".env", extra="ignore")


def get_settings():
    return Settings()
