from pydantic import BaseModel, Field


class FilterParams(BaseModel):
    limit: int = Field(10, ge=1, le=100)
    page: int = Field(1, ge=1)
