from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from src.core import db


class UnitOfWork:
    def __init__(
        self,
        *,
        use_postgres: bool = True,
        use_mongodb: bool = False,
    ):
        self._postgres_manager = None
        self._mongo_manager = None
        self._postgres_session = None
        self._mongo_session = None

        if use_postgres:
            self._postgres_manager = db.get_postgres_manager()

        if use_mongodb:
            self._mongo_manager = db.get_mongo_manager()

    async def __aenter__(self):
        if self._postgres_manager:
            self._postgres_session = await self._postgres_manager.session
            await self._postgres_session.begin()

        if self._mongo_manager:
            self._mongo_session = await self._mongo_manager.start_session()
            self._mongo_session.start_transaction()

        return self

    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        try:
            if self._postgres_session:
                if exc_type is not None:
                    await self._postgres_session.rollback()
                else:
                    await self._postgres_session.commit()
            if self._mongo_session:
                if exc_type is not None:
                    await self._mongo_session.abort_transaction()
                else:
                    await self._mongo_session.commit_transaction()
        finally:
            if self._postgres_session:
                await self._postgres_session.close()
            if self._mongo_session:
                await self._mongo_session.end_session()

    @property
    def postgres_session(self) -> AsyncSession:
        if self._postgres_session is None:
            raise RuntimeError

        return self._postgres_session

    @property
    def mongo_session(self):
        if self._mongo_session is None:
            raise RuntimeError

        return self._mongo_session


def get_uow(
    *,
    use_postgres: bool = True,
    use_mongodb: bool = False,
) -> UnitOfWork:
    return UnitOfWork(use_postgres=use_postgres, use_mongodb=use_mongodb)
