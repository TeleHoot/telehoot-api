from typing import Any

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models, schemas

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def create_test_helper(
    *,
    path: str,
    data: dict[str, Any],
    status_code: int,
    client: httpx.AsyncClient,
    session: AsyncSession | None = None,
) -> str | None:
    response: httpx.Response = await client.post(path, json=data)
    response_data = response.json()

    if 200 <= status_code < 300:  # noqa: PLR2004
        assert "detail" not in response_data
    else:
        assert "detail" in response_data
        return None

    for given_field, given_value in data.items():
        assert response_data.get(given_field) == given_value

    assert "id" in response_data
    quiz_id: str = response_data["id"]

    if session:
        quiz = await session.get(models.Organization, quiz_id)

        assert quiz is not None

        for given_field, given_value in data.items():
            assert getattr(quiz, given_field) == given_value
    return quiz_id


@pytest.mark.xfail(reason="needs mongodb")
async def test_create_quiz_success(
    user_client: httpx.AsyncClient,
    db_session: AsyncSession,
    organization: models.Organization,
    user: models.User,
):
    data = schemas.quizzes.Create(name="Brainrot Quiz")
    path = f"/organizations/{organization.id}/quizzes/"
    await create_test_helper(
        path=path,
        data=data.model_dump(),
        status_code=status.HTTP_201_CREATED,
        client=user_client,
        session=db_session,
    )

    read_response: httpx.Response = await user_client.get(path)
    read_response_data = read_response.json()

    assert "detail" not in read_response_data

    assert "author" in read_response_data
    assert read_response_data["author"]["id"] == user.id

    assert read_response_data.get("organization_id") == organization.id

    assert read_response_data.get("questions_count") == 0
