from typing import Annotated

from fastapi import Depends

from src import core
from src.app import services
from src.core.db import get_db_manager

settings = core.config.get_settings()
db_manager = get_db_manager()


UsersService = Annotated[services.Users, Depends()]
