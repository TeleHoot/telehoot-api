from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Base schema for Organization with common fields."""
    name: str = Field(..., max_length=255)
    description: str = Field(..., max_length=500)
    is_verified: bool = Field(default=False)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an Organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an Organization."""
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=500)
    is_verified: bool | None = None
    deleted_at: datetime | None = None


class OrganizationRead(OrganizationBase):
    """Schema for reading an Organization with all fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)