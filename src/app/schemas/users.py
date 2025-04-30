import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core

Username = Annotated[str, Field(min_length=5, max_length=32)]
TelegramUsername = Annotated[str, Field(min_length=5, max_length=32)]
FirstName = Annotated[str, Field(min_length=1, max_length=50)]
LastName = Annotated[str, Field(min_length=1, max_length=50)]


class Base(BaseModel):
    telegram_id: int
    username: Username | None = None
    telegram_username: TelegramUsername
    first_name: FirstName
    last_name: LastName | None = None
    is_admin: bool = False
    photo_url: str | None


class Create(Base):
    pass


class Read(Base):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    username: Username | None = None
    telegram_username: TelegramUsername | None = None
    first_name: FirstName | None = None
    last_name: LastName | None = None
    photo_url: str | None = None


class TelegramAuth(Base):
    is_admin: Annotated[bool, Field(exclude=True)] = False
    auth_date: int
    hash: str


class Filters(core.schemas.BaseFilters):
    is_admin: bool | None = None


class SortFields(enum.StrEnum):
    USERNAME = "username"
    TELEGRAM_USERNAME = "telegram_username"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
