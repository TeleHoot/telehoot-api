import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src import core
from src.app import schemas


class Base(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = False


class Create(Base):
    pass


class Update(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


class Read(Base):
    id: UUID
    organization_id: UUID
    author: schemas.users.Read
    created_at: datetime
    updated_at: datetime
    questions_count: int = 0

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


class Filters(core.schemas.BaseFilters):
    organization_id: UUID | None = None
    author_id: UUID | None = None
    name: str | None = None
    is_public: bool | None = None


class SortFields(enum.StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    IS_PUBLIC = "is_public"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
