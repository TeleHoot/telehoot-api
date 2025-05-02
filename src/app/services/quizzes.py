from uuid import UUID

from src import core
from src.app import models, repositories, schemas


class Quizzes(
    core.services.BaseCRUD[
        schemas.quizzes.Create,
        schemas.quizzes.Read,
        schemas.quizzes.Update,
        schemas.quizzes.Filters,
        schemas.quizzes.SortParams,
        models.Quiz,
    ]
):
    def __init__(self):
        self.repo = repositories.Quizzes()
        self.questions_repo = repositories.Questions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.quizzes.Create,
            read_schema=schemas.quizzes.Read,
            update_schema=schemas.quizzes.Update,
            filters_schema=schemas.quizzes.Filters,
        )

    async def read_by_id(self, uow: core.UnitOfWork, quiz_id: UUID) -> schemas.quizzes.Read:
        quiz = await super().read_by_id(uow, quiz_id)
        quiz.questions_count = await self.questions_repo.get_count_by_quiz_id(uow, quiz_id=quiz_id)
        return quiz

    async def read_many(
        self,
        uow: core.UnitOfWork,
        filters: schemas.quizzes.Filters | None = None,
        sorting: schemas.quizzes.SortParams | None = None,
        pagination: core.schemas.PaginationParams | None = None,
    ) -> list[schemas.quizzes.Read]:
        quizzes = await super().read_many(uow, filters, sorting, pagination)

        for quiz in quizzes:
            quiz.questions_count = await self.questions_repo.get_count_by_quiz_id(
                uow, quiz_id=quiz.id
            )

        return quizzes
