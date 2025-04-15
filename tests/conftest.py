from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.core.db import get_sql_manager
from src.main import app

pytest_plugins = ["pytest_asyncio"]

db_manager = get_sql_manager()


@pytest.fixture(scope="session")
async def setup_db_schema() -> AsyncGenerator[None]:
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.create_all)
    yield
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:
    async with db_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def anonim_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """
    Yields:
        AsyncClient: Non-authenticated client
    """
    app.dependency_overrides[db_manager.get_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client

    app.dependency_overrides = {}
