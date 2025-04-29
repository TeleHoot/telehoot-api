import enum
from typing import Annotated

from pydantic import UUID4, Field

from src import core


class QuestionType(enum.StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    ORDERING = "ordering"


class QuestionContent(core.models.mongo.BaseMixin, core.models.mongo.SoftDelete):
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    media_path: str | None = None


class QuestionAnswer(core.models.mongo.BaseMixin, core.models.mongo.SoftDelete):
    text: Annotated[str, Field(min_length=1, max_length=500)]
    is_correct: bool
    order: Annotated[int, Field(ge=0, le=100)]


class Question(core.models.mongo.BaseMixin, core.models.mongo.SoftDelete):
    quiz_id: UUID4
    order: Annotated[int, Field(ge=0, le=1000)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    type: QuestionType
    question_content: QuestionContent
    answers: Annotated[list[QuestionAnswer], Field(min_length=1, max_length=4)]
