from src import core
from src.app import models, repositories, schemas


class Users(
    core.services.BaseCRUD[
        schemas.users.Create, schemas.users.Read, schemas.users.Update, models.User
    ]
):
    def __init__(self):
        super().__init__(
            repositories.Users(),
            create_schema=schemas.users.Create,
            read_schema=schemas.users.Read,
            update_schema=schemas.users.Update,
        )

    @core.utils.decorators.log_operation
    async def read_by_telegram_id(self, uow: core.uow.UnitOfWork, telegram_id: int):
        user = await self.read_by_telegram_id(uow, telegram_id)

        if not user:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__, f"telegram_id={telegram_id}"
            )

        return await self._validate_data(user)
