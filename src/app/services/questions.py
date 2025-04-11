
from beanie import PydanticObjectId

from src.app.repositories.questions import QuestionsRepository
from src.core.db import MultiDBUnitOfWork
from src.core.repositories.exceptions import DatabaseError


class QuestionService:
    def __init__(self, repository: QuestionsRepository):
        self.repo = repository

    async def unsafe_update_sequence(
            self,
            uow: MultiDBUnitOfWork,
            question_id: PydanticObjectId
    ):

        try:
            # First valid update
            await self.repo.update_by_id(uow, question_id, {"order": 999})

            # Second update that will fail
            await self.repo.update_by_id(uow, question_id, {"non_existing_field": 123})

        except Exception as e:
            raise DatabaseError("Questions service", "Transaction failed") from e