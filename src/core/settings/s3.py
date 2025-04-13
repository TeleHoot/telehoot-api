from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from src.core import settings


class S3ServiceSettings(BaseModel):
    BUCKET_NAME: str = "telehoot"
    ENDPOINT: str = "localhost:9000"
    ACCESS_KEY: str = "user"
    SECRET_KEY: str = "passpasspass"
    REGION: str = ""
    REQUIRE_TLS: bool = False
    IS_PROXY_REQUIRED: bool = True
    INTERNAL_URL: str = "http://localhost:9000"

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="S3_"
    )
