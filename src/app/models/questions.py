from beanie import DocumentWithSoftDelete

from src.core.models import BaseMixin


class Question(DocumentWithSoftDelete, BaseMixin):
    quiz_id: str
    order: int
    title: str
    type: str
