import time
from typing import Annotated

from pydantic import BaseModel, Field


class Event(BaseModel):
    timestamp: Annotated[float, Field(default_factory=lambda: time.time())]
