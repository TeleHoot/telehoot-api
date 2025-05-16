from __future__ import annotations

import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core

from . import users as schemas_users

Description = Annotated[str | None, Field(max_length=500)]


class Base(BaseModel):
    name: str
    description: Description = None
    is_public: bool = False

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class Create(Base):
    pass


class Update(BaseModel):
    name: str | None = None
    description: Description = None
    is_public: bool | None = None


class Read(Base):
    id: UUID
    organization_id: UUID
    author: schemas_users.Read
    created_at: datetime
    updated_at: datetime
    questions_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    organization_id: UUID | None = None
    author_id: UUID | None = None
    name: str | None = None
    is_public: bool | None = None


class SortFields(enum.StrEnum):
    NAME = "name"
    IS_PUBLIC = "is_public"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
