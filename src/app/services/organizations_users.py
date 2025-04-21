from src import core
from src.app import models, repositories, schemas


class OrganizationsUsers(
    core.services.BaseCRUD[
        schemas.organizations_users.Create,
        schemas.organizations_users.Read,
        schemas.organizations_users.Update,
        models.OrganizationUser,
    ]
):
    def __init__(self):
        self.repo = repositories.OrganizationsUsers()
        super().__init__(
            self.repo,
            create_schema=schemas.organizations_users.Create,
            read_schema=schemas.organizations_users.Read,
            update_schema=schemas.organizations_users.Update,
        )
