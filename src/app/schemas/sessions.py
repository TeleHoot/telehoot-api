import enum
from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.app import models

if TYPE_CHECKING:
    from src.app import schemas


class Base(BaseModel):
    join_code: Annotated[str, Field(min_length=4, max_length=4)]
    status: models.SessionStatus = models.SessionStatus.WAITING

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class Create(BaseModel):
    pass


class Update(BaseModel):
    status: models.SessionStatus | None = None


class Read(Base):
    id: UUID
    quiz: "schemas.quizzes.Read"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    quiz_id: UUID | None = None
    join_code: str | None = None
    status: models.SessionStatus | None = None


class SortFields(enum.StrEnum):
    JOIN_CODE = "join_code"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class SessionEventType(enum.StrEnum):
    JOIN = "join"
    LEAVE = "leave"
    START = "start"
    ANSWER = "answer"
    NEXT = "next"
    FINISH = "finish"
    ERROR = "error"
    END = "end"


class SessionEvent(core.schemas.websocket.EventBase):
    type: SessionEventType


class UserJoinedEvent(SessionEvent):
    type: SessionEventType = SessionEventType.JOIN
    user_id: UUID
    participant_id: UUID | None = None
    username: str
    photo_url: str | None = None
    role: models.ParticipantRole


class UserLeftEvent(SessionEvent):
    type: SessionEventType = SessionEventType.LEAVE
    user_id: UUID
    participant_id: UUID


class NextQuestionEvent(SessionEvent):
    type: SessionEventType = SessionEventType.NEXT
    current_question_index: int


class SessionStartedEvent(NextQuestionEvent):
    type: SessionEventType = SessionEventType.START
    current_question_index: int = 1


class SessionEndedEvent(SessionEvent):
    type: SessionEventType = SessionEventType.END
    results: list["schemas.participant_answers.Read"] | None = None


class ErrorEvent(SessionEvent):
    type: SessionEventType = SessionEventType.ERROR
    error_code: str
    message: str | None = None
    code: int
