import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core

Name = Annotated[str, Field(min_length=2, max_length=64)]
Description = Annotated[str, Field(max_length=500)]


class Base(BaseModel):
    name: Name
    description: Description | None = None


class Create(Base):
    pass


class Update(BaseModel):
    name: Name | None = None
    description: Description | None = None


class Read(Base):
    id: UUID
    created_at: datetime
    updated_at: datetime
    image_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    pass


class SortFields(enum.StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
