from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClientSession
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import src.app
from src import core
from src.app import models, schemas
from src.app.api import dependencies
from src.main import app

postgres_manager = core.db.get_postgres_manager()
mongo_manager = core.db.get_mongo_manager()


@pytest.fixture(scope="session", autouse=True)
def create_app_test():
    with TestClient(src.app.create_app()):
        yield


@pytest.fixture(scope="session")
async def setup_db_schema() -> None:
    async with postgres_manager.engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.create_all)

        if tables := core.models.sqlalchemy.Base.metadata.tables.values():
            table_names = ",".join(f'"{table.name}"' for table in tables)
            await conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:
    async with postgres_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def mongo_session() -> AsyncGenerator[AsyncIOMotorClientSession]:
    session = await mongo_manager.get_session()
    session.start_transaction()

    try:
        yield session
    finally:
        await session.abort_transaction()
        await session.end_session()


@pytest.fixture(scope="function")
async def client(
    monkeypatch: pytest.MonkeyPatch,
    db_session: AsyncSession,
    mongo_session: AsyncIOMotorClientSession,
) -> AsyncGenerator[AsyncClient]:
    async def patched_aenter(self):  # noqa: RUF029
        self._postgres_session = db_session
        self._mongo_session = mongo_session
        return self

    async def patched_aexit(*args, **kwargs):
        pass

    monkeypatch.setattr(core.UnitOfWork, "__aenter__", patched_aenter)
    monkeypatch.setattr(core.UnitOfWork, "__aexit__", patched_aexit)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def user(db_session: AsyncSession) -> models.User:
    user = models.User(
        username="Tung Tung Tung Sahur",
        is_admin=False,
        telegram_id=12345,
        telegram_username="Sahur228",
        first_name="Lirili",
        last_name="Larila",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_client(client: AsyncClient, user: models.User) -> Generator[AsyncClient, Any, Any]:
    app.dependency_overrides[dependencies.permissions.get_current_user] = (
        lambda: schemas.users.Read.model_validate(user)
    )

    yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> models.User:
    user = models.User(
        username="Mr. Pudge",
        is_admin=True,
        telegram_id=54321,
        telegram_username="Pudger228",
        first_name="Pudge",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_client(client: AsyncClient, admin_user: models.User) -> Generator[AsyncClient, Any, Any]:
    app.dependency_overrides[dependencies.permissions.get_current_user] = (
        lambda: schemas.users.Read.model_validate(admin_user)
    )

    yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def organization(db_session: AsyncSession) -> models.Organization:
    org = models.Organization(name="Bondito")
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
async def membership_owner(
    db_session: AsyncSession, organization: models.Organization, user: models.User
) -> models.Membership:
    membership = models.Membership(
        organization_id=organization.id,
        user_id=user.id,
        role=models.membership.UserRoles.OWNER,
        status=models.membership.Statuses.APPROVED,
    )
    db_session.add(membership)
    await db_session.flush()
    await db_session.refresh(membership)
    return membership


@pytest.fixture(scope="function")
async def membership_editor(
    db_session: AsyncSession, organization: models.Organization, user: models.User
) -> models.Membership:
    membership = models.Membership(
        organization_id=organization.id,
        user_id=user.id,
        role=models.membership.UserRoles.EDITOR,
        status=models.membership.Statuses.APPROVED,
    )
    db_session.add(membership)
    await db_session.flush()
    await db_session.refresh(membership)
    return membership


@pytest.fixture(scope="function")
async def quiz(
    user_client: AsyncClient, organization: models.Organization, user: models.User
) -> schemas.quizzes.Read:
    response = await user_client.post(
        f"/organizations/{organization.id}/quizzes",
        json={
            "name": "Test Quiz",
            "description": "Sample quiz for testing",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    quiz_data = response.json()
    return schemas.quizzes.Read.model_validate(quiz_data)


@pytest.fixture(scope="function")
async def session(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    membership_editor: models.Membership,
):
    response = await user_client.post(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions"
    )
    assert response.status_code == status.HTTP_201_CREATED
    session_data = response.json()
    return schemas.sessions.Read.model_validate(session_data)
