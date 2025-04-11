from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=255)]
    balance: float = Field(ge=0, default=0.0)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
