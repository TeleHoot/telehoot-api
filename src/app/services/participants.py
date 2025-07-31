from src import core
from src.app import models, repositories, schemas


class Participants(
    core.services.BaseCRUD[
        schemas.participants.Create,
        schemas.participants.Read,
        schemas.participants.Update,
        schemas.participants.Filters,
        schemas.participants.SortParams,
        models.Participant,
    ]
):
    def __init__(self):
        self.repo = repositories.Participants()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.participants.Create,
            read_schema=schemas.participants.Read,
            update_schema=schemas.participants.Update,
            filters_schema=schemas.participants.Filters,
        )
