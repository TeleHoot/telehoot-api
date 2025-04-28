from datetime import UTC, datetime

from pydantic import BaseModel, Field


class BaseMixin(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
