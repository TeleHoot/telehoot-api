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
    assert response.status_code == status.HTTP_201_CREATED
    session_data = response.json()
    assert session_data["status"] == models.SessionStatus.WAITING


async def test_get_sessions(
    user_client: AsyncClient,
    organization: models.Organization,
    quiz: models.Quiz,
    session: models.Session,
):
    response = await user_client.get(
        f"/organizations/{organization.id}/quizzes/{quiz.id}/sessions"
    )
    assert response.status_code == status.HTTP_200_OK
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == str(session.id)
    assert sessions[0]["hosts"][0]["role"] == "host"
