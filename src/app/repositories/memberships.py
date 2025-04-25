from src import core
from src.app import models


class Memberships(core.repositories.sqlalchemy.BaseCRUD[models.Membership]):
    def __init__(self):
        super().__init__(models.Membership)
