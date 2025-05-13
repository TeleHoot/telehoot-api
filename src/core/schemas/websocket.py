import time

from pydantic import BaseModel, Field


class SessionEventBase(BaseModel):
    timestamp: float = Field(default_factory=time.time)


class ErrorEvent(SessionEventBase):
    error_code: str
    message: str
    code: int
