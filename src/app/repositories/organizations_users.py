from src import core
from src.app import models


class OrganizationsUsers(core.repositories.sqlalchemy.BaseCRUD[models.OrganizationUser]):
    def __init__(self):
        super().__init__(models.OrganizationUser)
