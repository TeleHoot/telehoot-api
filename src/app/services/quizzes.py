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
        super().__init__(
            repo=self.repo,
            create_schema=schemas.quizzes.Create,
            read_schema=schemas.quizzes.Read,
            update_schema=schemas.quizzes.Update,
            filters_schema=schemas.quizzes.Filters,
        )
