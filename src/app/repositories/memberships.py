from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from src import core
from src.app import models


class Memberships(core.repositories.sqlalchemy.BaseCRUD[models.Membership]):
    def __init__(self):
        super().__init__(models.Membership)

    @core.utils.decorators.log_operation
    async def read_many(
        self,
        uow: core.uow.UnitOfWork,
        organization_id: UUID | None,
        user_id: UUID | None,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[models.Membership]:
        try:
            session = uow.postgres_session

            query = select(self.model)

            if organization_id:
                query = query.where(self.model.organization_id == organization_id)

            if user_id:
                query = query.where(self.model.user_id == user_id)

            query = query.offset((page - 1) * limit).limit(limit)

            result = await session.scalars(query)
            return result.all()
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @core.utils.decorators.log_operation
    async def read_by_organization_and_user_id(
        self, uow: core.uow.UnitOfWork, organization_id: UUID, user_id: UUID
    ) -> models.Membership | None:
        try:
            session = uow.postgres_session
            query = (
                select(self.model)
                .where(self.model.organization_id == organization_id)
                .where(self.model.user_id == user_id)
            )
            user = await session.scalar(query)

            if not user:
                self.logger.info(
                    "User in organization not found",
                    extra={
                        "organization_id": organization_id,
                        "user_id": user_id,
                        "exists": False,
                    },
                )
            return user
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
