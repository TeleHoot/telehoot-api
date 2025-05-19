from typing import Any

import httpx
import pytest
from beanie import PydanticObjectId
from fastapi import status
from motor.motor_asyncio import AsyncIOMotorClientSession

from src.app import models, schemas

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def create_test_helper(
    *,
    path: str,
    data: dict[str, Any],
    status_code: int,
    client: httpx.AsyncClient,
    session: AsyncIOMotorClientSession | None = None,
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
    question_id: str = response_data["id"]

    if session:
        question = await models.Question.find_one(
            models.Question.id == PydanticObjectId(question_id), session=session
        )

        assert question is not None

    return question_id


async def test_create_question_success(
    user_client: httpx.AsyncClient,
    mongo_session: AsyncIOMotorClientSession,
    organization: models.Organization,
    user: models.User,
    quiz: models.Quiz,
):
    answers = [
        schemas.questions.AnswerBase(text="Shrapnel", is_correct=False, order=0),
        schemas.questions.AnswerBase(text="Meat Hook", is_correct=True, order=1),
    ]

    data = schemas.questions.Create(
        order=0,
        weight=1,
        title="Pudge first skill?",
        type=models.question.QuestionType.SINGLE_CHOICE,
        answers=answers,
    )

    path = f"/quizzes/{quiz.id}/questions"
    await create_test_helper(
        path=path,
        data=data.model_dump(),
        status_code=status.HTTP_201_CREATED,
        client=user_client,
        session=mongo_session,
    )
