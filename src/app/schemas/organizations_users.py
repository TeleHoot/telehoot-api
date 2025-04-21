from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app import models
from src.app.schemas import organizations, users


class Base(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: models.UserRoles


class Create(Base):
    pass


class Update(BaseModel):
    role: models.UserRoles | None = None


class Read(Base):
    id: UUID
    organization: organizations.Read
    user: users.Read
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
