from typing import Annotated

from pydantic import BaseModel, Field


class FilterParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    limit: Annotated[int, Field(ge=1, le=100)] = 10
