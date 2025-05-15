import enum
from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.app import models

if TYPE_CHECKING:
    from src.app import schemas

SessionNickname = Annotated[str, Field(max_length=64)]


class Base(BaseModel):
    session_nickname: SessionNickname
    role: models.ParticipantRole = models.ParticipantRole.PARTICIPANT

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class Create(Base):
    user_id: UUID


class Update(BaseModel):
    session_nickname: SessionNickname | None = None
    role: models.ParticipantRole | None = None


class Read(Base):
    id: UUID
    user_id: UUID
    session_id: UUID
    user: "schemas.users.Read"
    session: "schemas.sessions.Read"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    user_id: UUID | None = None
    session_id: UUID | None = None
    role: models.ParticipantRole | None = None


class SortFields(enum.StrEnum):
    SESSION_NICKNAME = "session_nickname"
    ROLE = "role"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
