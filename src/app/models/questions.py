from beanie import DocumentWithSoftDelete

from src import core


class Question(DocumentWithSoftDelete, core.models.mongo.BaseMixin):
    quiz_id: str
    order: int
    title: str
    type: str
