from uuid import UUID

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

    @core.utils.decorators.log_operation
    async def read_many_by_organization(self, uow, organization_id: UUID):
        users = await self.repo.read_many_by_organization(uow, organization_id)

        if not users:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__, f"org_id={organization_id}"
            )

        return [await self._validate_data(user) for user in users]

    @core.utils.decorators.log_operation
    async def read_by_user_id(self, uow, user_id: UUID):
        user = await self.repo.read_by_user_id(uow, user_id)

        if not user:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__, f"user_id={user_id}"
            )

        return await self._validate_data(user)
