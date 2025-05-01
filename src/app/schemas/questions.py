import enum
from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src import core
from src.app.models.question import MediaType, QuestionType

Order = Annotated[int, Field(ge=0, le=1000)]
Title = Annotated[str, Field(min_length=1, max_length=200)]
Type = Annotated[QuestionType, Field(description="Тип вопроса")]
Description = Annotated[str, Field(min_length=1, max_length=1000)]
AnswerText = Annotated[str, Field(min_length=1, max_length=500)]
Answers = Annotated[list["AnswerBase"], Field(min_length=1, max_length=4)]


class ContentBase(BaseModel):
    description: Description
    media_type: MediaType = MediaType.NONE
    media_path: Annotated[str | None, Field(description="Путь к медиафайлу")] = None

    @model_validator(mode="after")
    def validate_media_path(self) -> Self:
        if self.media_type != MediaType.NONE and not self.media_path:
            raise ValueError("Media path is required when media_type is specified")
        return self

    model_config = ConfigDict(
        from_attributes=True,
    )


class AnswerBase(BaseModel):
    text: AnswerText
    is_correct: bool
    order: Annotated[int, Field(ge=0, le=100, description="Порядок ответа")]

    model_config = ConfigDict(
        from_attributes=True,
    )


class QuestionBase(BaseModel):
    order: Order
    title: Title
    type: Type
    question_content: ContentBase
    answers: Answers

    @model_validator(mode="after")
    def validate_answers(self) -> Self:
        if self.type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
            correct_answers = [ans for ans in self.answers if ans.is_correct]
            if not correct_answers:
                raise ValueError("At least one correct answer is required for choice questions")
            if self.type == QuestionType.SINGLE_CHOICE and len(correct_answers) > 1:
                raise ValueError("Single choice questions can have only one correct answer")
        elif self.type == QuestionType.TEXT and len(self.answers) != 1:
            raise ValueError("Text questions must have exactly one answer")
        return self


class Create(QuestionBase):
    pass


class Update(BaseModel):
    order: Order | None = None
    title: Title | None = None
    type: Type | None = None
    question_content: ContentBase | None = None
    answers: Answers | None = None


class Read(QuestionBase):
    id: PydanticObjectId
    quiz_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class Filters(core.schemas.BaseFilters):
    quiz_id: UUID | None
    type: Type | None = None


class SortFields(enum.StrEnum):
    ORDER = "order"
    TITLE = "title"
    TYPE = "type"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
