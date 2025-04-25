from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SessionParticipantBase(BaseModel):
    user_id: str
    username: str
    score: int = 0
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class SessionParticipantCreate(SessionParticipantBase):
    pass


class SessionParticipantRead(SessionParticipantBase):
    session_id: str


class SessionBase(BaseModel):
    quiz_id: str
    host_id: str
    status: str = "waiting"
    current_question_index: int = 0
    settings: dict = Field(default_factory=dict)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    current_question_index: Optional[int] = None
    settings: Optional[dict] = None


class SessionRead(SessionBase):
    id: str
    participants: List[SessionParticipantRead]
    created_at: datetime
    updated_at: datetime 