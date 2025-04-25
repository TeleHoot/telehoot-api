import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.core.schemas.filter import SortOrderField


class SortFields(enum.StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.PageLimitParams):
    sort_by: SortFields | None = None
    order_by: SortOrderField = SortOrderField.ASCENDING


class Base(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=64)]
    description: Annotated[str | None, Field(max_length=500)] = None


class Create(Base):
    pass


class Update(BaseModel):
    name: Annotated[str | None, Field(min_length=2, max_length=64)] = None
    description: Annotated[str | None, Field(max_length=500)] = None


class Read(Base):
    id: UUID
    created_at: datetime
    updated_at: datetime
    image_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    pass
