from src import core
from src.app import models


class Organizations(core.repositories.sqlalchemy.BaseCRUD[models.Organization]):
    def __init__(self):
        super().__init__(models.Organization)
