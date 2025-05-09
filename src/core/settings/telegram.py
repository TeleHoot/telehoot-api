import hashlib
import hmac
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class TelegramOAuthSettings(BaseSettings):
    BOT_TOKEN: str = "Some token"
    MINI_APP_SECRET: str = "WebAppData"

    @property
    def BOT_SECRET(self) -> bytes:
        return hashlib.sha256(self.BOT_TOKEN.encode("utf-8")).digest()

    @property
    def MINI_APP_SECRET_KEY(self) -> bytes:
        return hmac.new(
            self.MINI_APP_SECRET.encode(), self.BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

    def verify_hash(
        self,
        data_check_string: str,
        received_hash: str,
        auth_type: Literal["widget", "mini_app"] = "widget",
    ) -> bool:
        """
        Validates the hash for different authorization types.

        :param data_check_string: The string to validate (without hash)
        :param received_hash: The hash received from Telegram
        :param auth_type: The authorization type ('widget' or 'mini_app')
        Returns:
            bool
        """
        secret = self.BOT_SECRET if auth_type == "widget" else self.MINI_APP_SECRET_KEY

        computed_hash = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()

        return hmac.compare_digest(computed_hash, received_hash)

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="TG_"
    )
