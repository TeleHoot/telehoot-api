from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class MongoDBSettings(BaseSettings):
    HOST: str = "localhost"
    USER: str = "mongo"
    PORT: int = 27017
    PASSWORD: str = "mongo"
    DB: str = "admin"

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="MONGO_"
    )

    @property
    def DSN(self) -> MongoDsn:
        return MongoDsn.build(
            scheme="mongodb",
            username=self.USER,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=self.DB,
        )

    @property
    def URL(self) -> str:
        return str(self.DSN)
