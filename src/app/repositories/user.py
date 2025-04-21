from sqlalchemy import select

from src import core
from src.app import models


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    @core.utils.decorators.log_operation
    async def read_by_telegram_id(
        self, uow: core.uow.UnitOfWork, telegram_id: int
    ) -> models.User | None:
        try:
            session = uow.postgres_session
            query = select(self.model).where(self.model.telegram_id == telegram_id)
            result = await session.scalars(query)
            user = result.first()

            if not user:
                self.logger.info(
                    "User not found by Telegram ID",
                    extra={"telegram_id": telegram_id, "exists": False},
                )
            return user
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
