import enum
from datetime import datetime
from typing import Annotated, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class RangeFilter[T](BaseModel):
    from_: Annotated[T | None, Field(alias="from")] = None
    to: T | None = None

    @model_validator(mode="after")
    def check_all_none(self) -> Self:
        if self.from_ is None and self.to is None:
            raise ValueError("Both 'from' and 'to' cannot be None")
        return self

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.from_ is not None and self.to is not None:
            try:
                if self.to < self.from_:  # type: ignore[operator]
                    raise ValueError("'to' must be greater or equal to 'from'")
            except TypeError:
                raise ValueError("Type doesn't support comparison") from None
        return self

    model_config = ConfigDict(serialize_by_alias=True)


class BaseFilters(BaseModel):
    created_at: RangeFilter[datetime] | None = None
    updated_at: RangeFilter[datetime] | None = None


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class SortOrderField(enum.StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class SortParams(BaseModel):
    order_by: SortOrderField = SortOrderField.ASCENDING
