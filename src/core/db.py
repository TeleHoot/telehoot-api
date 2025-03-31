from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core import config, utils


@utils.Singleton
class DatabaseManager:
    def __init__(self):
        self.settings = config.get_settings()
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    def _create_engine(self) -> AsyncEngine:
        return create_async_engine(
            self.settings.POSTGRES.URL,
            echo=self.settings.DEBUG,
            poolclass=NullPool if self.settings.DEBUG else AsyncAdaptedQueuePool,
            pool_recycle=900 if not self.settings.DEBUG else -1,
        )

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory.begin() as session:
            yield session

    # for manual testing
    @asynccontextmanager
    async def session_context(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory.begin() as session:
            yield session


def get_db_manager():
    return DatabaseManager()
