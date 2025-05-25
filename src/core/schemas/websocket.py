import time

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    timestamp: float = Field(default_factory=time.time)


class ErrorEvent(EventBase):
    error_code: str
    message: str
    code: int
