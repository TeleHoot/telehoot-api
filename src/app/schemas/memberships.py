from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app import models
from src.app.schemas import organizations, users


class Base(BaseModel):
    role: models.UserRoles
    status: models.MembershipStatuses


class Create(Base):
    organization_id: UUID
    user_id: UUID


class Update(BaseModel):
    role: models.UserRoles | None = None
    status: models.MembershipStatuses | None = None


class Read(Base):
    organization: organizations.Read
    user: users.Read
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
