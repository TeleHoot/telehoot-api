import time

from pydantic import BaseModel


class Event(BaseModel):
    timestamp: float = time.time()
