from src import core
from src.app import models


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)
