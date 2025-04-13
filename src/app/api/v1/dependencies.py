from typing import Annotated

from fastapi import Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import services
from src.core.db import get_db_manager

settings = core.config.get_settings()
db_manager = get_db_manager()

DBSession = Annotated[AsyncSession, Depends(db_manager.get_session)]


UsersService = Annotated[services.Users, Depends()]
OrganizationService = Annotated[services.Organizations, Depends()]

LimitPageQuery = Annotated[core.schemas.query_filter.FilterParams, Query()]
