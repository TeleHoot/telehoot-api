from uuid import UUID

from src import core
from src.app import models


class Questions(core.repositories.mongo.BaseCRUD[models.Question]):
    def __init__(self):
        super().__init__(models.Question)

    async def get_count_by_quiz_id(self, uow: core.UnitOfWork, quiz_id: UUID) -> int:
        return await self.model.find_many({"quiz_id": quiz_id}, session=uow.mongo_session).count()
