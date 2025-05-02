from src import core
from src.app import models
from src.core import custom_types
from src.core.uow import UnitOfWork


class Questions(core.repositories.mongo.BaseCRUD[models.Question]):
    def __init__(self):
        super().__init__(models.Question)

    async def get_count_by_quiz_id(self, uow: UnitOfWork, quiz_id: custom_types.EntityID) -> int:
        return await self.model.find_many({"quiz_id": quiz_id}, session=uow.mongo_session).count()
