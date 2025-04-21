import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class TelegramOAuthSettings(BaseSettings):
    BOT_TOKEN: str = "Some token"
    ALGORITHM: str = "SHA256"

    @property
    def BOT_SECRET(self):
        return hashlib.sha256(self.BOT_TOKEN.encode("UTF-8")).digest()

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="TG_"
    )
