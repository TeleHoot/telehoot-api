from src import core
from src.app import models


class Questions(core.repositories.mongo.BaseCRUD[models.Question]):
    def __init__(self):
        super().__init__(models.Question)
