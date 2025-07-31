from src import core
from src.app import models


class ParticipantAnswers(core.repositories.sqlalchemy.BaseCRUD[models.ParticipantAnswer]):
    def __init__(self):
        super().__init__(models.ParticipantAnswer)
