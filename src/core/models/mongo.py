from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field
from uuid_v7.base import uuid7


class BaseMixin(BaseModel):
    uid: UUID = Field(default_factory=uuid7)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
