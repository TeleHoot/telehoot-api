from uuid import UUID

from src import core
from src.app import models, repositories, schemas


class Memberships(
    core.services.BaseCRUD[
        schemas.memberships.Create,
        schemas.memberships.Read,
        schemas.memberships.Update,
        models.Membership,
    ]
):
    def __init__(self):
        self.repo = repositories.Memberships()
        super().__init__(
            self.repo,
            create_schema=schemas.memberships.Create,
            read_schema=schemas.memberships.Read,
            update_schema=schemas.memberships.Update,
        )

    @core.utils.decorators.log_operation
    async def read_many(
        self,
        uow: core.uow.UnitOfWork,
        organization_id: UUID | None,
        user_id: UUID | None,
        page: int = 1,
        limit: int = 10,
    ):
        users = await self.repo.read_many(uow, organization_id, user_id, page, limit)

        return [await self._validate_data(user) for user in users]
