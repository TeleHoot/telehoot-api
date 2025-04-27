import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class UserSortFields(enum.StrEnum):
    USERNAME = "username"
    TELEGRAM_USERNAME = "telegram_username"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class Base(BaseModel):
    username: Annotated[str, Field(min_length=5, max_length=32)]
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    photo_url: str | None = None


class Create(Base):
    telegram_id: int

    @computed_field
    @property
    def telegram_username(self) -> str:
        return self.username


class Read(Base):
    id: UUID
    telegram_id: int
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    telegram_username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    first_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    photo_url: str | None = None


class TelegramAuth(Base):
    id: Annotated[int, Field(alias="telegram_id")]
    auth_date: int
    hash: str

    model_config = ConfigDict(validate_by_alias=False, serialize_by_alias=True)
