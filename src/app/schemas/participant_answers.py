import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from src import core
from src.app import schemas

AnswerText = Annotated[str, Field(max_length=1000)]
PointsFilter = Annotated[int | None, Field(ge=0)]


class Base(BaseModel):
    text: AnswerText
    is_correct: bool = False
    points: PositiveInt = Field(default=0, ge=0)

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class Create(Base):
    participant_id: UUID
    question_id: PydanticObjectId


class Update(BaseModel):
    text: AnswerText | None = None
    is_correct: bool | None = None
    points: PositiveInt | None = Field(default=None, ge=0)


class Read(Base):
    participant_id: UUID
    question_id: PydanticObjectId
    participant: schemas.participants.Read
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    participant_id: UUID | None = None
    question_id: PydanticObjectId | None = None
    is_correct: bool | None = None
    points_from: PointsFilter = None
    points_to: PointsFilter = None


class SortFields(enum.StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    POINTS = "points"
    IS_CORRECT = "is_correct"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
