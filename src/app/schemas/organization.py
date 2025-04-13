from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=64)
    description: str = Field(..., max_length=500)


class OrganizationCreate(OrganizationBase): ...


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, max_length=64)
    description: str | None = Field(None, max_length=500)


class OrganizationRead(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
