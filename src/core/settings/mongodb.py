from pydantic import MongoDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import settings


class MongoDBSettings(BaseSettings):
    HOST: str = "localhost"
    INITDB_ROOT_USERNAME: str = "mongo"
    PORT: int = 27017
    INITDB_ROOT_PASSWORD: str = "mongo"
    INITDB_DATABASE: str = "mongo"
    IS_NEED_INIT_REPLICASET: bool = True

    model_config = SettingsConfigDict(
        env_file=settings.env_config.ENV_FILE_PATH, extra="ignore", env_prefix="MONGO_"
    )

    @computed_field
    @property
    def DSN(self) -> MongoDsn:
        return MongoDsn.build(
            scheme="mongodb",
            username=self.INITDB_ROOT_USERNAME,
            password=self.INITDB_ROOT_PASSWORD,
            host=self.HOST,
            port=self.PORT,
        )

    @computed_field
    @property
    def URL(self) -> str:
        return str(self.DSN)
