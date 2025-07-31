from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends

from src import core


def get_uow_factory(
    *,
    use_postgres: bool = True,
    use_mongodb: bool = False,
) -> Callable[[], AsyncGenerator[core.UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[core.UnitOfWork]:
        async with core.UnitOfWork(use_postgres=use_postgres, use_mongodb=use_mongodb) as uow:
            yield uow

    return _get_uow


Postgres = Annotated[core.UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
Mongo = Annotated[core.UnitOfWork, Depends(get_uow_factory(use_mongodb=True))]
Full = Annotated[core.UnitOfWork, Depends(get_uow_factory(use_postgres=True, use_mongodb=True))]
