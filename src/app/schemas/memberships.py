import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src import core
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


class Filters(core.schemas.BaseFilters):
    organization_id: UUID | None = None
    user_id: UUID | None = None
    role: models.UserRoles | None = None
    status: models.MembershipStatuses | None = None


class SortFields(enum.StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None
