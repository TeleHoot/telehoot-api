from src import core
from src.app import models


class Sessions(core.repositories.sqlalchemy.BaseCRUD[models.Session]):
    def __init__(self):
        super().__init__(models.Session)
