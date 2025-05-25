import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_session(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    membership_editor: models.Membership,
):
    response = await user_client.post(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions"
    )

    session_data = response.json()
    assert "detail" not in session_data
    assert session_data["status"] == models.SessionStatus.WAITING


async def test_get_session(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
):
    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}"
    )

    session_data = response.json()
    assert "detail" not in session_data
    assert session_data["id"] == str(session.id)
    assert session_data["hosts"][0]["role"] == "host"


async def test_get_sessions(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
):
    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions"
    )
    sessions_data = response.json()
    assert "detail" not in sessions_data
    assert len(sessions_data) == 1
    assert sessions_data[0]["id"] == str(session.id)
    assert sessions_data[0]["hosts"][0]["role"] == "host"


async def test_update_session(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
):
    response = await user_client.patch(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}",
        json={"status": "active"},
    )

    assert "detail" not in response.json()

    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}"
    )

    session_data = response.json()
    assert "detail" not in session_data

    assert session_data["status"] == "active"


async def test_delete_session(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
    db_session: AsyncSession,
):
    session_in_db = await db_session.scalar(select(models.Session))
    assert session_in_db is not None
    assert session_in_db.deleted_at is None

    response = await user_client.delete(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}",
    )
    assert "detail" not in response.json()

    session_in_db = await db_session.scalar(select(models.Session))
    assert session_in_db is not None
    assert session_in_db.deleted_at is not None

    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.xfail
async def test_admin_sees_deleted_session(
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
    db_session: AsyncSession,
    admin_client: AsyncClient,
):
    response = await admin_client.delete(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}",
    )
    assert "detail" not in response.json()

    response = await admin_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}"
    )

    response_data = response.json()
    assert "detail" not in response_data
    assert "id" in response_data
    assert response_data["id"] == str(session.id)
