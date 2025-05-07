from pydantic import RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class RedisSettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 6379
    PASSWORD: str = "somepassord"

    @computed_field
    @property
    def DSN(self) -> RedisDsn:
        return RedisDsn.build(
            scheme="redis",
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
        )

    @computed_field
    @property
    def URL(self) -> str:
        return str(self.DSN)

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="REDIS_"
    )
