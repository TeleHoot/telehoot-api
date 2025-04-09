import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class LoggerSettings(BaseSettings):
    LEVEL: int = logging.DEBUG
    FILE_PATH: str = "app.log"
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ACCESS_LOG: str = "access.log"
    MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="LOGGER_"
    )
