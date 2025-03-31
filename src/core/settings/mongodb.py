from pydantic import MongoDsn
from pydantic_settings import BaseSettings


class MongoDBSettings(BaseSettings):
    MONGO_HOST: str = "localhost"
    MONGO_USER: str = "mongo"
    MONGO_PORT: int = 27017
    MONGO_PASSWORD: str = "mongo"
    MONGO_DB: str = "admin"

    @property
    def DSN(self) -> MongoDsn:
        return MongoDsn.build(
            scheme="mongodb",
            username=self.MONGO_USER,
            password=self.MONGO_PASSWORD,
            host=self.MONGO_HOST,
            port=self.MONGO_PORT,
            path=self.MONGO_DB,
        )

    @property
    def URL(self) -> str:
        return str(self.DSN)
