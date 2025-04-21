from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.params import Query

from src import core
from src.app import schemas, services
from src.core.config import get_settings

UsersService = Annotated[services.Users, Depends()]
OrganizationService = Annotated[services.Organizations, Depends()]
OrganizationUserService = Annotated[services.OrganizationsUsers, Depends()]

PageLimitQuery = Annotated[core.schemas.query_filter.FilterParams, Query()]

settings = get_settings()


def get_uow_factory(
    *,
    use_postgres: bool = True,
    use_mongodb: bool = False,
) -> Callable[[], AsyncGenerator[core.uow.UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[core.uow.UnitOfWork]:
        async with core.uow.UnitOfWork(use_postgres=use_postgres, use_mongodb=use_mongodb) as uow:
            yield uow

    return _get_uow


PostgresUOW = Annotated[core.uow.UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
MongoUOW = Annotated[core.uow.UnitOfWork, Depends(get_uow_factory(use_mongodb=True))]
FullUOW = Annotated[
    core.uow.UnitOfWork, Depends(get_uow_factory(use_postgres=True, use_mongodb=True))
]

AuthService = Annotated[services.Authentication, Depends()]


async def get_current_user(
    request: Request,
    uow: PostgresUOW,
    auth_service: AuthService,
) -> schemas.users.Read:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise core.services.exceptions.AuthenticationError("Missing token")  # noqa: TRY003, EM101

    return await auth_service.read_user_by_token(uow, token)


AuthorizedUser = Annotated[schemas.users.Read, Depends(get_current_user)]
