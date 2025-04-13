from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Base(BaseModel):
    name: Annotated[str, Field(max_length=64)]
    description: Annotated[str, Field(max_length=500)]


class Create(Base):
    pass


class Update(BaseModel):
    name: Annotated[str | None, Field(max_length=64)] = None
    description: Annotated[str | None, Field(max_length=500)] = None


class Read(Base):
    id: UUID
    created_at: datetime
    updated_at: datetime
    image_url: HttpUrl | None = None

    model_config = ConfigDict(from_attributes=True)
