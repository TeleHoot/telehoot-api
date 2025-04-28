import enum
from datetime import datetime
from typing import Annotated, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseFilters(BaseModel):
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class SortOrderField(enum.StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class SortParams(BaseModel):
    order_by: SortOrderField = SortOrderField.ASCENDING
