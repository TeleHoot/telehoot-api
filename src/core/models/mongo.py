from datetime import UTC, datetime

from pydantic import BaseModel, Field

from typing import Annotated


class BaseMixin(BaseModel):
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]


class SoftDelete:
    deleted_at: Annotated[datetime | None, Field(default=None)]
