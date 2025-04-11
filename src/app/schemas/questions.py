from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class QuestionBase(BaseModel):
    quiz_id: str
    order: int
    title: str
    type: str

class QuestionCreate(QuestionBase):
    pass

class QuestionRead(QuestionBase):
    uid: UUID
    created_at: datetime
    updated_at: datetime
    _id: str
