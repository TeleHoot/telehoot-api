from typing import ClassVar

from sqlalchemy.orm import InstrumentedAttribute

from src import core
from src.app import models


class Quizzes(core.repositories.sqlalchemy.BaseCRUD[models.Quiz]):
    def __init__(self):
        super().__init__(models.Quiz)

    search_fields: ClassVar[list[InstrumentedAttribute]] = [models.Quiz.name]
