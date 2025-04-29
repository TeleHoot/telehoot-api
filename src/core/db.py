import logging
from collections.abc import Callable, Sequence
from typing import TypeVar

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core import config, utils

logger = logging.getLogger(__name__)

T = TypeVar("T")

settings = config.get_settings()


@utils.decorators.Singleton
class PostgresManager:
    def __init__(self):
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    @staticmethod
    def _create_engine() -> AsyncEngine:
        return create_async_engine(
            settings.POSTGRES.URL,
            echo=settings.DEBUG,
            poolclass=AsyncAdaptedQueuePool,
            pool_recycle=900,
        )

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False, autobegin=False
        )

    async def get_session(self) -> AsyncSession:
        return self.session_factory()


def get_postgres_manager() -> PostgresManager:
    return PostgresManager()


@utils.decorators.Singleton
class MongoDBManager:
    async def initialize(self):
        self.client = AsyncIOMotorClient(
            settings.MONGO.URL,
            serverSelectionTimeoutMS=5000,
        )

        await self.client.admin.command("ping")

    async def get_session(self) -> AsyncIOMotorClientSession:
        return await self.client.start_session()


def get_mongo_manager() -> MongoDBManager:
    return MongoDBManager()


async def init_mongo(aggregator: Callable[[], Sequence[type[Document]]]) -> None:
    """Initialize MongoDB connection with Beanie ODM.

    Args:
        aggregator: Function that returns a sequence of document model classes
    """
    try:
        mongo_manager = get_mongo_manager()
        await mongo_manager.initialize()

        await init_beanie(
            database=mongo_manager.client[settings.MONGO.INITDB_DATABASE],
            document_models=aggregator(),
            multiprocessing_mode=True,
        )
    except Exception as e:
        logger.exception("Failed to initialize MongoDB connection", extra={"error": str(e)})
        raise


def init_replica_set():
    client = None
    try:
        client = MongoClient(
            f"mongodb://{settings.MONGO.HOST}:{settings.MONGO.PORT}/",
            directConnection=True,
            username=settings.MONGO.INITDB_ROOT_USERNAME,
            password=settings.MONGO.INITDB_ROOT_PASSWORD,
            authSource="admin",
        )

        try:
            status = client.admin.command("replSetGetStatus")
            logger.info("Replica Set are already initialized: %s", status["set"])
            return
        except PyMongoError as e:
            if "NotYetInitialized" not in str(e):
                raise

        cfg = {
            "_id": "overleaf",
            "members": [{"_id": 0, "host": f"{settings.MONGO.HOST}:{settings.MONGO.PORT}"}],
        }

        logger.info("Initializing Replica Set...")
        client.admin.command("replSetInitiate", cfg)
        logger.info("Replica Set are successfully initialized")

    except Exception:
        logger.exception("Error while initializing Replica Set")
        raise
    finally:
        if client:
            client.close()
