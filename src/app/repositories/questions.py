
from beanie import PydanticObjectId

from src.app.models import Question
from src.core.db import MultiDBUnitOfWork

from src.core.repositories.abstract import AbstractCRUD

class QuestionsRepository(AbstractCRUD[Question]):
    def __init__(self):
        self.model = Question

    async def create(self, uow: MultiDBUnitOfWork, data: dict) -> Question:
        session = uow.get_mongo_session()
        question = Question(**data)
        await question.insert(session=session)
        return question

    async def update_by_id(
        self,
        uow: MultiDBUnitOfWork,
        question_id: PydanticObjectId,
        data: dict
    ) -> Question | None:
        session = uow.get_mongo_session()
        question = await self.model.get(question_id, session=session)
        if question:
            await question.set(data, session=session)
            return question
        return None

    # Implement other CRUD methods similarly with session handling