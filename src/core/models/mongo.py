from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field


class BaseMixin(BaseModel):
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
