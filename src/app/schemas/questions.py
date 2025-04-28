from typing import Optional, Annotated, List
from beanie import PydanticObjectId
from pydantic import BaseModel, Field, UUID4, conlist, field_validator, ConfigDict
from datetime import datetime

from pydantic_core.core_schema import FieldValidationInfo, ValidationInfo

from src.app.models.questions import MediaType, QuestionType

QuizId = Annotated[UUID4, Field(description="ID квиза, к которому относится вопрос")]
Order = Annotated[int, Field(ge=0, le=1000, description="Порядковый номер вопроса в квизе")]
Title = Annotated[str, Field(min_length=1, max_length=200, description="Текст вопроса")]
Type = Annotated[QuestionType, Field(description="Тип вопроса")]
Description = Annotated[str, Field(min_length=1, max_length=1000, description="Описание контента вопроса")]
AnswerText = Annotated[str, Field(min_length=1, max_length=500, description="Текст ответа")]

class ContentBase(BaseModel):
    description: Description
    media_type: MediaType = MediaType.NONE
    media_path: Optional[str] = Field(None, description="Путь к медиафайлу")

    @field_validator('media_path')
    @classmethod
    def validate_media_path(cls, v: Optional[str], info: FieldValidationInfo) -> Optional[str]:
        if info.data.get('media_type') != MediaType.NONE and not v:
            raise ValueError('Media path is required when media_type is specified')
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
    answers: conlist(AnswerBase, min_length=1, max_length=10)

    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v: List[AnswerBase], info: ValidationInfo) -> List[AnswerBase]:
        question_type = info.data.get('type')

        if question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            correct_answers = [ans for ans in v if ans.is_correct]
            if not correct_answers:
                raise ValueError('At least one correct answer is required for choice questions')
            if question_type == QuestionType.SINGLE_CHOICE and len(correct_answers) > 1:
                raise ValueError('Single choice questions can have only one correct answer')
        elif question_type == QuestionType.TEXT and len(v) != 1:
            raise ValueError('Text questions must have exactly one answer')
        return v

class Create(QuestionBase):
    pass

class Update(BaseModel):
    quiz_id: Optional[QuizId] = None
    order: Optional[Order] = None
    title: Optional[Title] = None
    type: Optional[Type] = None
    question_content: Optional[ContentBase] = None
    answers: Optional[conlist(AnswerBase, min_length=1, max_length=10)] = None

class Read(QuestionBase):
    id: Annotated[PydanticObjectId, Field(alias="_id")]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={PydanticObjectId: str},
        populate_by_name=True,
        from_attributes=True,
    )