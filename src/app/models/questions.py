from beanie import DocumentWithSoftDelete
from src import core

class Question(DocumentWithSoftDelete, core.models.mongo.BaseMixin):
    quiz_id: str
    order: int
    title: str
    type: str

    class Settings:
        use_state_management = True
        validate_on_save = True