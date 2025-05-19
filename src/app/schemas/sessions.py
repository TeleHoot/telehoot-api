import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.app import models

from . import participants as participant_schemas
from . import questions as question_schemas
from . import quizzes as quiz_schemas
from . import users as user_schemas


class Base(BaseModel):
    join_code: Annotated[
        str,
        Field(
            min_length=4, max_length=4, pattern=r"^\d+$", description="Must be exactly 4 digits"
        ),
    ]
    status: models.SessionStatus = models.SessionStatus.WAITING
    current_question_index: int = 0


class Create(BaseModel):
    pass


class Update(BaseModel):
    status: models.SessionStatus | None = None
    current_question_index: int | None = None


class Read(Base):
    id: UUID
    hosts: list[participant_schemas.Read]
    quiz: quiz_schemas.Read
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
    CANCEL = "cancel"
    SHOW_ANSWERS = "show_answers"


class SessionEvent(core.schemas.websocket.EventBase):
    type: SessionEventType


class UserJoinedEvent(SessionEvent):
    type: SessionEventType = SessionEventType.JOIN
    user_id: UUID | None = None
    participant_id: UUID | None = None
    username: str
    photo_url: str | None = None
    role: models.ParticipantRole | None = None


class UserLeftEvent(SessionEvent):
    type: SessionEventType = SessionEventType.LEAVE
    user_id: UUID | None = None
    participant_id: UUID


class NextQuestionEvent(SessionEvent):
    type: SessionEventType = SessionEventType.NEXT
    current_question_index: int = 0
    question: question_schemas.Read | None = None
    is_last_question: bool = False


class SessionStartedEvent(NextQuestionEvent):
    type: SessionEventType = SessionEventType.START


class SessionFinishedEvent(SessionEvent):
    type: SessionEventType = SessionEventType.FINISH


class SessionCanceledEvent(SessionEvent):
    type: SessionEventType = SessionEventType.CANCEL


class SessionAnsweredEvent(SessionEvent):
    type: SessionEventType = SessionEventType.ANSWER


class SessionShowedAnswersEvent(SessionEvent):
    type: SessionEventType = SessionEventType.SHOW_ANSWERS


class ErrorEvent(SessionEvent):
    type: SessionEventType = SessionEventType.ERROR
    error_code: str
    message: str | None = None
    code: int


class SessionResult(BaseModel):
    user: user_schemas.Read
    total_points: Annotated[int, Field(ge=0)]
