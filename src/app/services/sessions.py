from src import core
from src.app import models, repositories, schemas


class Sessions(
    core.services.BaseCRUD[
        schemas.sessions.Create,
        schemas.sessions.Read,
        schemas.sessions.Update,
        schemas.sessions.Filters,
        schemas.sessions.SortParams,
        models.Session,
    ]
):
    def __init__(self):
        self.repo = repositories.Sessions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.sessions.Create,
            read_schema=schemas.sessions.Read,
            update_schema=schemas.sessions.Update,
            filters_schema=schemas.sessions.Filters,
        )
