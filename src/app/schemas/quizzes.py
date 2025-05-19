from __future__ import annotations

import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from src import core

from . import organizations as organization_schemas
from . import users as user_schemas
from . import utils

Description = Annotated[str | None, Field(max_length=500)]
Name = Annotated[
    str, BeforeValidator(utils.validate_non_empty), Field(min_length=1, max_length=64)
]


class Base(BaseModel):
    name: Name
    description: Description = None
    is_public: bool = False

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class Create(Base):
    pass


class Update(BaseModel):
    name: Name | None = None
    description: Description = None
    is_public: bool | None = None


class Read(Base):
    id: UUID
    organization: organization_schemas.Read
    author: user_schemas.Read
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
