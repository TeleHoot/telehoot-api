from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class PostgreSQLSettings(BaseSettings):
    HOST: str = "localhost"
    USER: str = "postgres"
    PORT: int = 5432
    PASSWORD: str = "postgres"
    DB: str = "postgres"

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="POSTGRES_"
    )

    @property
    def DSN(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.USER,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=self.DB,
        )

    @property
    def URL(self) -> str:
        return str(self.DSN)
