from src import core
from src.app import repositories, schemas


class Organizations(
    core.services.BaseCRUD[
        schemas.OrganizationCreate, schemas.OrganizationRead, schemas.OrganizationUpdate
    ]
):
    def __init__(self):
        self.repo = repositories.Organizations()
        super().__init__(
            self.repo,
            create_schema=schemas.OrganizationCreate,
            read_schema=schemas.OrganizationRead,
            update_schema=schemas.OrganizationUpdate,
        )
