import logging
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import TypeVar

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import AsyncAdaptedQueuePool, NullPool
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
class SQLManager:
    def __init__(self):
        self._engine = self._create_engine()
        self._session_factory = self._create_session_factory()

    @staticmethod
    def _create_engine() -> AsyncEngine:
        return create_async_engine(
            settings.POSTGRES.URL,
            echo=settings.DEBUG,
            poolclass=NullPool if settings.DEBUG else AsyncAdaptedQueuePool,
            pool_recycle=900 if not settings.DEBUG else -1,
        )

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False, autobegin=False
        )

    async def get_session(self) -> AsyncSession:
        return self._session_factory()

    async def get_session_generator(self) -> AsyncGenerator[AsyncSession]:
        async with self._session_factory.begin() as session:
            yield session


def get_sql_manager():
    return SQLManager()


@utils.decorators.Singleton
class MongoDBManager:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None

    async def initialize(self):
        self.client = AsyncIOMotorClient(
            settings.MONGO.URL,
            serverSelectionTimeoutMS=5000,
        )

        await self.client.admin.command("ping")


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


class UnitOfWork:
    def __init__(
        self,
        sql_manager: SQLManager | None,
        mongo_manager: AsyncIOMotorClient | None,
    ):
        self._db_manager: SQLManager | None = sql_manager
        self._mongo_manager: AsyncIOMotorClient | None = mongo_manager
        self._sql_session = None
        self._mongo_session = None

    async def __aenter__(self):
        if self._db_manager:
            self._sql_session = await self._db_manager.get_session()
            await self._sql_session.begin()

        if self._mongo_manager:
            self._mongo_session = await self._mongo_manager.start_session()
            self._mongo_session.start_transaction()
        return self

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        try:
            if self._sql_session:
                if exc_type is not None:
                    await self._sql_session.rollback()
                else:
                    await self._sql_session.commit()
            if self._mongo_session:
                if exc_type is not None:
                    await self._mongo_session.abort_transaction()
                else:
                    await self._mongo_session.commit_transaction()
        finally:
            if self._sql_session:
                await self._sql_session.close()
            if self._mongo_session:
                await self._mongo_session.end_session()

    @property
    def sql_session(self) -> AsyncSession:
        assert self._sql_session is not None

        return self._sql_session

    @property
    def mongo_session(self):
        assert self._mongo_session is not None

        return self._mongo_session


class UoWManager:
    def __init__(self, *, use_sqlalchemy: bool = True, use_mongodb: bool = False):
        self.use_sqlalchemy = use_sqlalchemy
        self.use_mongodb = use_mongodb

    async def __call__(self) -> AsyncGenerator[UnitOfWork]:
        sql_manager = get_sql_manager() if self.use_sqlalchemy else None
        mongo_client = get_mongo_manager().client if self.use_mongodb else None
        async with UnitOfWork(sql_manager=sql_manager, mongo_manager=mongo_client) as uow:
            yield uow
