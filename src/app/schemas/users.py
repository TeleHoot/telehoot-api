from __future__ import annotations

import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src import core

Username = Annotated[str, Field(min_length=5, max_length=32)]
TelegramUsername = Annotated[str, Field(min_length=5, max_length=32)]
FirstName = Annotated[str, Field(min_length=1, max_length=50)]
LastName = Annotated[str | None, Field(min_length=1, max_length=50)]


class Base(BaseModel):
    username: Username
    first_name: FirstName
    last_name: LastName = None
    photo_url: str | None = None


class Create(Base):
    telegram_id: int

    @computed_field
    @property
    def telegram_username(self) -> str:
        return self.username


class Read(Base):
    id: UUID
    telegram_username: TelegramUsername
    telegram_id: int
    is_admin: bool
    created_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    username: Username | None = None
    telegram_username: TelegramUsername | None = None
    first_name: FirstName | None = None
    last_name: LastName = None
    photo_url: str | None = None


class TelegramAuth(Base):
    id: Annotated[int, Field(alias="telegram_id")]
    auth_date: int
    hash: str

    model_config = ConfigDict(validate_by_alias=False, serialize_by_alias=True)


class Filters(core.schemas.BaseFilters):
    is_admin: bool | None = None


class SortFields(enum.StrEnum):
    USERNAME = "username"
    TELEGRAM_USERNAME = "telegram_username"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
