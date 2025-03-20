from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings


class DatabaseManager:
    def __init__(self, pool: bool = True):
        self.settings = get_settings()
        self.engine = self._create_engine() if pool else self._create_null_pool_engine()
        self.session_factory = self._create_session_factory()

    def _create_engine(self) -> AsyncEngine:
        return create_async_engine(
            str(self.settings.DATABASE_URL),
            echo=False,
            poolclass=AsyncAdaptedQueuePool,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=900,
        )

    def _create_null_pool_engine(self) -> AsyncEngine:
        return create_async_engine(
            str(self.settings.DATABASE_URL),
            echo=False,
            poolclass=NullPool,
            future=True,
        )

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_async_session(self) -> AsyncSession:
        return self.session_factory()


manager = DatabaseManager()
