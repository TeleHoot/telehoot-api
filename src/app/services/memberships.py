from src import core
from src.app import models, repositories, schemas


class Memberships(
    core.services.BaseCRUD[
        schemas.memberships.Create,
        schemas.memberships.Read,
        schemas.memberships.Update,
        schemas.memberships.Filters,
        schemas.memberships.SortParams,
        models.Membership,
    ]
):
    def __init__(self):
        self.repo = repositories.Memberships()
        super().__init__(
            self.repo,
            create_schema=schemas.memberships.Create,
            read_schema=schemas.memberships.Read,
            update_schema=schemas.memberships.Update,
            filters_schema=schemas.memberships.Filters,
        )
