from __future__ import annotations

import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from src import core

from . import utils

Name = Annotated[
    str, BeforeValidator(utils.validate_non_empty), Field(min_length=2, max_length=64)
]
Description = Annotated[str | None, Field(max_length=500)]


class Base(BaseModel):
    name: Name
    description: Description = None


class Create(Base):
    pass


class Update(BaseModel):
    name: Name | None = None
    description: Description = None
    image_path: str | None = None


class Read(Base):
    id: UUID
    created_at: datetime
    updated_at: datetime
    image_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


Read.model_rebuild()


class Filters(core.schemas.BaseFilters):
    pass


class SortFields(enum.StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class ReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
