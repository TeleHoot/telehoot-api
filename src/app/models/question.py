import enum
from typing import Annotated
from uuid import UUID

from beanie import DocumentWithSoftDelete
from pydantic import BaseModel, Field

from src import core


class QuestionType(enum.StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    ORDERING = "ordering"


class QuestionAnswer(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=500)]
    order: Annotated[int, Field(ge=0, le=100)]
    is_correct: bool


class Question(core.models.mongo.BaseMixin, DocumentWithSoftDelete):
    quiz_id: UUID
    order: Annotated[int, Field(ge=0, le=1000)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    weight: Annotated[int, Field(ge=0, le=100)] = 0
    type: QuestionType
    description: Annotated[str | None, Field(max_length=500)] = None
    media_path: str | None = None
    answers: Annotated[list[QuestionAnswer], Field(min_length=1, max_length=4)]
