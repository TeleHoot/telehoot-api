from datetime import datetime
from typing import List

from beanie import Document
from pydantic import Field


class SessionParticipant(Document):
    user_id: str
    username: str
    score: int = 0
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "session_participants"


class Session(Document):
    id: str = Field(alias="_id")
    quiz_id: str
    host_id: str
    status: str = "waiting"
    current_question_index: int = 0
    settings: dict = Field(default_factory=dict)
    participants: List[SessionParticipant] = Field(default_factory=list)
    
    class Settings:
        name = "sessions"
        indexes = [
            "quiz_id",
            "host_id",
            "status",
        ] 