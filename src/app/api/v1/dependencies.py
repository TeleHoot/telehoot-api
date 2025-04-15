from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.params import Query

from src import core
from src.app import services

UsersService = Annotated[services.Users, Depends()]
OrganizationService = Annotated[services.Organizations, Depends()]

PageLimitQuery = Annotated[core.schemas.query_filter.FilterParams, Query()]


def get_uow_factory(
    *,
    use_postgres: bool = True,
    use_mongodb: bool = False,
) -> Callable[[], AsyncGenerator[core.uow.UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[core.uow.UnitOfWork]:
        async with core.uow.get_uow(use_postgres=use_postgres, use_mongodb=use_mongodb) as uow:
            yield uow

    return _get_uow


PostgresUOW = Annotated[core.uow.UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
MongoUOW = Annotated[core.uow.UnitOfWork, Depends(get_uow_factory(use_mongodb=True))]
FullUOW = Annotated[
    core.uow.UnitOfWork, Depends(get_uow_factory(use_postgres=True, use_mongodb=True))
]
