import pytest
from fastapi import status
from httpx import AsyncClient

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
):
    response = await user_client.delete(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}",
    )
    assert "detail" not in response.json()

    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions/{session.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
