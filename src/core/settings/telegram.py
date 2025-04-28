import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class TelegramOAuthSettings(BaseSettings):
    BOT_TOKEN: str = "Some token"

    @property
    def BOT_SECRET(self) -> bytes:
        return hashlib.sha256(self.BOT_TOKEN.encode("utf-8")).digest()

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="TG_"
    )
