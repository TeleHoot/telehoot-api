import logging
from collections.abc import Callable, Sequence
from typing import TypeVar

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
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
        self._session_factory = self._create_session_factory()

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
        return self._session_factory()


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
