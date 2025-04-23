from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from src import core
from src.app import models


class OrganizationsUsers(core.repositories.sqlalchemy.BaseCRUD[models.OrganizationUser]):
    def __init__(self):
        super().__init__(models.OrganizationUser)

    @core.utils.decorators.log_operation
    async def read_many_by_organization(
        self,
        uow: core.uow.UnitOfWork,
        organization_id: UUID,
    ) -> Sequence[models.OrganizationUser] | None:
        try:
            session = uow.postgres_session
            query = select(self.model).where(self.model.organization_id == organization_id)
            result = await session.scalars(query)

            if not result:
                self.logger.info(
                    "Users not found by Organization ID",
                    extra={"org_id": organization_id, "exists": False},
                )
            return result.all()
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @core.utils.decorators.log_operation
    async def read_by_user_id(
        self, uow: core.uow.UnitOfWork, user_id: UUID
    ) -> models.OrganizationUser | None:
        try:
            session = uow.postgres_session
            query = select(self.model).where(self.model.user_id == user_id)
            result = await session.scalars(query)
            user = result.first()

            if not user:
                self.logger.info(
                    "User in org not found by user ID",
                    extra={"user_id": user_id, "exists": False},
                )
            return user
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
