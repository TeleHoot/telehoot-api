from datetime import datetime
from typing import Annotated

from beanie import PydanticObjectId
from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo, ValidationInfo

from src.app.models.questions import MediaType, QuestionType

QuizId = Annotated[UUID4, Field(...)]
Order = Annotated[int, Field(ge=0, le=1000)]
Title = Annotated[str, Field(min_length=1, max_length=200)]
Type = Annotated[QuestionType, Field(description="Тип вопроса")]
Description = Annotated[str, Field(min_length=1, max_length=1000)]
AnswerText = Annotated[str, Field(min_length=1, max_length=500)]


class ContentBase(BaseModel):
    description: Description
    media_type: MediaType = MediaType.NONE
    media_path: str | None = Field(None, description="Путь к медиафайлу")

    @field_validator("media_path")
    @classmethod
    def validate_media_path(cls, v: str | None, info: FieldValidationInfo) -> str | None:
        if info.data.get("media_type") != MediaType.NONE and not v:
            raise ValueError("Media path is required when media_type is specified")  # noqa: EM101 TRY003
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class AnswerBase(BaseModel):
    text: AnswerText
    is_correct: bool = Field(description="Является ли ответ правильным")
    order: Annotated[int, Field(ge=0, le=100, description="Порядок ответа")]

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class QuestionBase(BaseModel):
    quiz_id: QuizId
    order: Order
    title: Title
    type: Type
    question_content: ContentBase
    answers: Annotated[list[AnswerBase], Field(min_length=1, max_length=4)]

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: list[AnswerBase], info: ValidationInfo) -> list[AnswerBase]:
        question_type = info.data.get("type")

        if question_type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
            correct_answers = [ans for ans in v if ans.is_correct]
            if not correct_answers:
                raise ValueError("At least one correct answer is required for choice questions")  # noqa: EM101 TRY003
            if question_type == QuestionType.SINGLE_CHOICE and len(correct_answers) > 1:
                raise ValueError("Single choice questions can have only one correct answer")  # noqa: EM101 TRY003
        elif question_type == QuestionType.TEXT and len(v) != 1:
            raise ValueError("Text questions must have exactly one answer")  # noqa: EM101 TRY003
        return v


class Create(QuestionBase):
    pass


class Update(BaseModel):
    quiz_id: QuizId | None = None
    order: Order | None = None
    title: Title | None = None
    type: Type | None = None
    question_content: ContentBase | None = None
    answers: Annotated[list[AnswerBase] | None, Field(min_length=1, max_length=4)] = None


class Read(QuestionBase):
    id: Annotated[PydanticObjectId, Field(alias="_id")]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(
        json_encoders={PydanticObjectId: str},
        populate_by_name=True,
        from_attributes=True,
    )
