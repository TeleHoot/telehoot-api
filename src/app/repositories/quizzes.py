from src import core
from src.app import models


class Quizzes(core.repositories.sqlalchemy.BaseCRUD[models.Quiz]):
    def __init__(self):
        super().__init__(models.Quiz)
