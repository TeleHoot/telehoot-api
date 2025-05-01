from src import core
from src.app import models, repositories, schemas
from src.core.uow import UnitOfWork


class Users(
    core.services.BaseCRUD[
        schemas.users.Create,
        schemas.users.Read,
        schemas.users.Update,
        schemas.users.Filters,
        schemas.users.SortParams,
        models.User,
    ]
):
    def __init__(self):
        self.repo = repositories.Users()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.users.Create,
            read_schema=schemas.users.Read,
            update_schema=schemas.users.Update,
            filters_schema=schemas.users.Filters,
        )

    @core.utils.decorators.log_operation
    async def read_by_telegram_id(self, uow: UnitOfWork, telegram_id: int):
        user = await self.repo.read_by_telegram_id(uow, telegram_id)

        if not user:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__, f"telegram_id={telegram_id}"
            )

        return await self._validate_data(user)
