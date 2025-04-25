import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core


class UserSortFields(enum.StrEnum):
    USERNAME = "username"
    TELEGRAM_USERNAME = "telegram_username"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class Base(BaseModel):
    telegram_id: int
    username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    telegram_username: Annotated[str, Field(min_length=5, max_length=32)]
    firstname: Annotated[str, Field(min_length=1, max_length=50)]
    lastname: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    is_admin: bool = False
    photo_url: str | None


class Create(Base):
    pass


class Read(Base):
    id: UUID
    deleted_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    telegram_username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    firstname: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    lastname: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    photo_url: str | None = None


class TelegramAuth(Base):
    is_admin: Annotated[bool, Field(exclude=True)] = False
    auth_date: int
    hash: str


class Filters(core.schemas.BaseFilters):
    is_admin: bool | None = None
