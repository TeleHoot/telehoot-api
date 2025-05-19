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

    if status_code >= status.HTTP_400_BAD_REQUEST:
        assert "detail" in response_data
        return None
    assert "detail" not in response_data

    for given_field, given_value in data.items():
        assert response_data.get(given_field) == given_value

    assert "id" in response_data
    quiz_id: str = response_data["id"]

    if session:
        quiz = await session.get(models.Quiz, quiz_id)
        assert quiz is not None

        for given_field, given_value in data.items():
            assert getattr(quiz, given_field) == given_value
    return quiz_id


@pytest.mark.parametrize(
    "data",
    [
        {"name": True, "is_public": True},
        {"name": "      ", "is_public": True},
        {"name": "TestQuiz", "description": "x" * 501, "is_public": True},
        {"description": "Test", "is_public": False},
    ],
)
async def test_create_quiz_fail_validation(
    data: dict[str, Any],
    user_client: httpx.AsyncClient,
    organization: models.Organization,
):
    path = f"/organizations/{organization.id}/quizzes"
    await create_test_helper(
        path=path, data=data, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, client=user_client
    )


async def test_create_quiz_success(
    user_client: httpx.AsyncClient,
    db_session: AsyncSession,
    organization: models.Organization,
    user: models.User,
):
    data = schemas.quizzes.Create(name="Brainrot Quiz")
    path = f"/organizations/{organization.id}/quizzes"
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

    created_quiz = read_response_data[0]

    assert "author" in created_quiz
    assert created_quiz["author"]["id"] == str(user.id)

    assert "organization" in created_quiz
    assert created_quiz["organization"]["id"] == str(organization.id)

    assert created_quiz.get("questions_count") == 0


async def test_quiz_questions_count(
    user_client: httpx.AsyncClient,
    db_session: AsyncSession,
    organization: models.Organization,
    user: models.User,
):
    data = schemas.quizzes.Create(name="Brainrot Quiz 2", is_public=True)
    path = f"/organizations/{organization.id}/quizzes"
    quiz_id = await create_test_helper(
        path=path,
        data=data.model_dump(),
        status_code=status.HTTP_201_CREATED,
        client=user_client,
        session=db_session,
    )

    questions_num = 3

    for i in range(questions_num):
        question_data = {
            "order": i,
            "title": f"Question {i}",
            "type": "multiple_choice",
            "answers": [
                {"text": "Option 1", "is_correct": True, "order": 0},
                {"text": "Option 2", "is_correct": False, "order": 1},
            ],
        }
        response = await user_client.post(
            f"/quizzes/{quiz_id}/questions",
            json=question_data,
        )

        assert "detail" not in response.json()

    response = await user_client.get(path + f"/{quiz_id}")

    assert response.json().get("questions_count") == questions_num


async def test_quiz_update_validation(
    user_client: httpx.AsyncClient,
    db_session: AsyncSession,
    user: models.User,
    organization: models.Organization,
):
    path = f"/organizations/{organization.id}/quizzes"
    quiz_data = {
        "name": "Dota2 Quiz",
        "description": "Pudge",
        "is_public": True,
    }
    quiz_id = await create_test_helper(
        path=path, data=quiz_data, status_code=status.HTTP_201_CREATED, client=user_client
    )

    response = await user_client.patch(path + f"/{quiz_id}", json={"name": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    update_data = {
        "name": "Updated Quiz Name",
        "is_public": False,
    }
    response = await user_client.patch(path + f"/{quiz_id}", json=update_data)

    response_data = response.json()

    assert "detail" not in response_data

    assert response_data.get("name") == update_data["name"]
    assert response_data.get("is_public") == update_data["is_public"]

    assert response_data.get("description") == quiz_data["description"]
