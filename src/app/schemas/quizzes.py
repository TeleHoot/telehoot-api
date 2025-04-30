import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src import core


class Base(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = False


class Create(Base):
    organization_id: UUID


class Update(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


class Read(Base):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    organization_id: UUID | None = None
    name: str | None = None
    is_public: bool | None = None


class SortFields(enum.StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    IS_PUBLIC = "is_public"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
