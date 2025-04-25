from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import models, schemas
from src.app.api.v1 import dependencies
from src.main import app

postgres_manager = core.db.get_postgres_manager()


@pytest.fixture(scope="session")
async def setup_db_schema() -> AsyncGenerator[None]:
    async with core.db.get_postgres_manager().engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.create_all)
    yield
    async with core.db.get_postgres_manager().engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:
    async with postgres_manager._session_factory.begin() as session:  # noqa: SLF001
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def client(
    monkeypatch: pytest.MonkeyPatch, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient]:
    async def patched_aenter(self):  # noqa: RUF029
        self._postgres_session = db_session
        return self

    async def patched_aexit(*args, **kwargs):
        pass

    monkeypatch.setattr(core.uow.UnitOfWork, "__aenter__", patched_aenter)
    monkeypatch.setattr(core.uow.UnitOfWork, "__aexit__", patched_aexit)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client


@pytest.fixture(scope="function")
def user_client(client: AsyncClient, user: models.User) -> AsyncClient:
    app.dependency_overrides[dependencies.get_current_user] = (
        lambda: schemas.users.Read.model_validate(user)
    )
    return client


@pytest.fixture(scope="function")
async def user(db_session: AsyncSession) -> models.User:
    user = models.User(
        username="Tung Tung Tung Sahur",
        is_admin=False,
        telegram_id=12345,
        telegram_username="Tung Tung Tung Sahur",
        first_name="Lirili",
        last_name="Larila",
    )
    db_session.add(user)
    await db_session.flush()
    return user
