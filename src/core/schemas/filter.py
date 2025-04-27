import enum
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class SortOrderField(enum.StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class BaseFilters(BaseModel):
    created_at: tuple[datetime | None, datetime | None] | None = None
    updated_at: tuple[datetime | None, datetime | None] | None = None

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def check_none_tuple(cls, value: tuple | None):
        if isinstance(value, tuple) and all(v is None for v in value):
            return None
        return value
