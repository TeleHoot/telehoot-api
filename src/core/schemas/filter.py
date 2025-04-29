import enum
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class BaseFilters(BaseModel):
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None

    @model_validator(mode="after")
    def validate_range_fields_match(self):
        from_base_names = [
            field_name[:-5]
            for field_name in self.__class__.model_fields.keys()  # noqa: SIM118
            if field_name.endswith("_from")
        ]
        to_base_names = [
            field_name[:-3]
            for field_name in self.__class__.model_fields.keys()  # noqa: SIM118
            if field_name.endswith("_to")
        ]

        if from_base_names != to_base_names:
            raise ValueError("Some '_from' fields lack corresponding '_to' fields or vice versa")

        return self

    @model_validator(mode="after")
    def validate_ranges(self):
        for field_name in self.__class__.model_fields.keys():  # noqa: SIM118
            if field_name.endswith("_from"):
                base_name = field_name[:-5]
                to_field = base_name + "_to"

                from_value, to_value = getattr(self, field_name), getattr(self, to_field)

                if from_value is not None and to_value is not None:
                    try:
                        if to_value < from_value:
                            raise ValueError(
                                f"'{to_field}' must be greater than or equal to '{field_name}'"
                            )
                    except TypeError:
                        raise ValueError(
                            f"Types of '{field_name}' and '{to_field}' do not support comparison"
                        ) from None
        return self


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class SortOrderField(enum.StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class SortParams(BaseModel):
    order_by: SortOrderField = SortOrderField.ASCENDING
