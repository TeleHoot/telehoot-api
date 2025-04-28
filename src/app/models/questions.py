from typing import Annotated

from beanie import DocumentWithSoftDelete
from pydantic import Field, UUID4, conlist
import enum
from src import core


class MediaType(enum.StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    NONE = "none"


class QuestionType(enum.StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    ORDERING = "ordering"


class QuestionContent(DocumentWithSoftDelete, core.models.mongo.BaseMixin):
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    media_type: MediaType = MediaType.NONE
    media_path: str | None = None


class QuestionAnswer(DocumentWithSoftDelete, core.models.mongo.BaseMixin):
    text: Annotated[str, Field(min_length=1, max_length=500)]
    is_correct: bool
    order: Annotated[int, Field(ge=0, le=100)]


class Question(DocumentWithSoftDelete, core.models.mongo.BaseMixin):
    quiz_id: UUID4
    order: Annotated[int, Field(ge=0, le=1000)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    type: QuestionType
    question_content: QuestionContent
    answers: conlist(QuestionAnswer, min_length=1, max_length=10)
