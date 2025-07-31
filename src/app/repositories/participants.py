from src import core
from src.app import models


class Participants(core.repositories.sqlalchemy.BaseCRUD[models.Participant]):
    def __init__(self):
        super().__init__(models.Participant)
