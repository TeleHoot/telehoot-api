from src import core
from src.app import models, repositories, schemas


class Questions(
    core.services.BaseCRUD[
        schemas.questions.Create, schemas.questions.Read, schemas.questions.Update, models.Question
    ]
):
    def __init__(self):
        super().__init__(
            repositories.Questions(),
            create_schema=schemas.questions.Create,
            read_schema=schemas.questions.Read,
            update_schema=schemas.questions.Update,
        )
        self.repo = repositories.Questions()
