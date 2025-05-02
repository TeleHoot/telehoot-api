import enum
from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src import core
from src.app.models.question import QuestionType

Order = Annotated[int, Field(ge=0, le=1000)]
Title = Annotated[str, Field(min_length=1, max_length=200)]
Type = Annotated[QuestionType, Field(description="Тип вопроса")]
AnswerText = Annotated[str, Field(min_length=1, max_length=500)]
Answers = Annotated[list["AnswerBase"], Field(min_length=1, max_length=4)]
Weight = Annotated[int, Field(ge=0, le=100)]
Description = Annotated[str | None, Field(min_length=1, max_length=1000)]
Media = Annotated[str | None, Field(description="Путь к медиафайлу")]


class AnswerBase(BaseModel):
    text: AnswerText
    is_correct: bool
    order: Annotated[int, Field(ge=0, le=100, description="Порядок ответа")]
    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    order: Order
    title: Title
    type: Type
    weight: Weight = 0
    description: Description = None
    media_path: Media = None
    answers: Answers

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

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
    weight: Weight | None = None
    description: Description = None
    media_path: Media = None
    answers: Answers | None = None


class Read(QuestionBase):
    id: PydanticObjectId
    quiz_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    quiz_id: UUID | None
    type: Type | None = None


class SortFields(enum.StrEnum):
    ORDER = "order"
    TITLE = "title"
    TYPE = "type"
    WEIGHT = "weight"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
