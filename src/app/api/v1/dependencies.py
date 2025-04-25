from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.params import Query
from fastapi.security import APIKeyCookie

from src import core
from src.app import schemas, services
from src.core.config import get_settings

UsersService = Annotated[services.Users, Depends()]
OrganizationService = Annotated[services.Organizations, Depends()]
MembershipsService = Annotated[services.Memberships, Depends()]

PaginationQuery = Annotated[core.schemas.PageLimitParams, Query()]

OrganizationsSortQuery = Annotated[schemas.organizations.SortParams, Query()]

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

cookie = APIKeyCookie(
    name=settings.SESSION_COOKIE_NAME,
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str, Depends(cookie)],
    uow: PostgresUOW,
    auth_service: AuthService,
) -> schemas.users.Read:
    if not token:
        raise core.services.exceptions.AuthenticationError("No session found")  # noqa: TRY003, EM101
    return await auth_service.read_user_by_token(uow, token)


CurrentUser = Annotated[schemas.users.Read, Depends(get_current_user)]


def get_active_user(current_user: CurrentUser) -> schemas.users.Read:
    if current_user.deleted_at is not None:
        raise core.services.exceptions.AuthenticationError("User is deleted")  # noqa: TRY003, EM101

    return current_user


ActiveUser = Annotated[schemas.users.Read, Depends(get_active_user)]
