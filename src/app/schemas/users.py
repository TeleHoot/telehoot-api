from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    is_admin: Annotated[bool, Field(default=False)]
    telegram_id: int
    username: Annotated[str | None, Field(min_length=5, max_length=32)]
    telegram_username: Annotated[str, Field(min_length=5, max_length=32)]
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str | None, Field(min_length=1, max_length=50)]
    photo_url: str


class Create(Base):
    pass


class Read(Base):
    id: UUID
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
