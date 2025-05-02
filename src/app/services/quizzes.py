from src import core
from src.app import models, repositories, schemas
from src.core import custom_types, services
from src.core.uow import UnitOfWork


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
        self.question_repo = repositories.Questions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.quizzes.Create,
            read_schema=schemas.quizzes.Read,
            update_schema=schemas.quizzes.Update,
            filters_schema=schemas.quizzes.Filters,
        )

    async def read_by_id(self, uow: UnitOfWork, entity_id: custom_types.EntityID) -> schemas.quizzes.Read:
        entity = await super().read_by_id(uow, entity_id)
        data = await self._dump_data(entity)
        data["questions_count"] = await self.question_repo.get_count(uow, quiz_id=entity_id)
        return self.read_schema.model_validate(data)

    async def read_many(
            self,
            uow: UnitOfWork,
            filters: schemas.quizzes.Filters | None = None,
            sorting: schemas.quizzes.SortParams | None = None,
            pagination: core.schemas.PaginationParams | None = None,
    ) -> list[schemas.quizzes.Read]:
        entities = await super().read_many(uow, filters, sorting, pagination)
        dumped_entities = [await self._dump_data(entity) for entity in entities]

        updated_entities = []
        for entity in dumped_entities:
            questions_count = await self.question_repo.get_count(uow, quiz_id=entity["id"])
            updated_entity = {**entity, "questions_count": questions_count}
            updated_entities.append(updated_entity)

        return [self.read_schema.model_validate(data) for data in updated_entities]
