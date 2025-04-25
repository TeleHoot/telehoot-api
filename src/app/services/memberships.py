from uuid import UUID

from src import core
from src.app import models, repositories, schemas
from src.core.services.base import EntityID
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation


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

    @log_operation
    async def read_many(
        self,
        uow: UnitOfWork,
        organization_id: UUID | None,
        user_id: UUID | None,
        page: int = 1,
        limit: int = 10,
    ) -> list[schemas.memberships.Read]:
        return await super().read_many(
            uow=uow,
            page=page,
            limit=limit,
            filters={"user_id": user_id, "organization_id": organization_id}
            if user_id or organization_id
            else None,
        )

    @log_operation
    async def read_by_id(
        self, uow: UnitOfWork, organization_id: EntityID, user_id: EntityID
    ) -> schemas.memberships.Read:
        return await super().read_by_id(
            uow=uow, entity_id={"organization_id": organization_id, "user_id": user_id}
        )
