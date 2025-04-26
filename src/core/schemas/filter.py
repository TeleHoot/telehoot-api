import enum
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class SortOrderField(enum.StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class BaseFilters(BaseModel):
    created_at: tuple[datetime | None, datetime | None] | None = None
    updated_at: tuple[datetime | None, datetime | None] | None = None
