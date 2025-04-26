import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSortFields(enum.StrEnum):
    USERNAME = "username"
    TELEGRAM_USERNAME = "telegram_username"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class Base(BaseModel):
    id: int
    username: Annotated[str, Field(min_length=5, max_length=32)]
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)]
    photo_url: str | None


class Create(Base):
    pass


class Read(Base):
    id: UUID  # type: ignore[valid-type]
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    telegram_username: Annotated[str | None, Field(min_length=5, max_length=32)] = None
    first_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    photo_url: str | None = None


class TelegramAuth(Base):
    auth_date: int
    hash: str
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)] = None
    photo_url: str | None = None

    @property
    def telegram_id(self) -> int:
        return self.id

    @property
    def telegram_username(self) -> str:
        return self.username
