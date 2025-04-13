from src import core
from src.app import models, repositories, schemas


class Users(
    core.services.BaseCRUD[schemas.UserCreate, schemas.UserRead, schemas.UserCreate, models.User]
):
    def __init__(self):
        self.repo = repositories.Users()
        super().__init__(
            self.repo,
            create_schema=schemas.UserCreate,
            read_schema=schemas.UserRead,
            update_schema=schemas.UserCreate,
        )
