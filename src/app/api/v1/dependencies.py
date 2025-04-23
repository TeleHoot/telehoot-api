from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.params import Query
from fastapi.security import APIKeyCookie

from src import core
from src.app import models, schemas, services
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


async def get_active_user(current_user: CurrentUser) -> schemas.users.Read:  # noqa: RUF029
    if current_user.deleted_at is not None:
        raise core.services.exceptions.AuthenticationError("User is deleted")  # noqa: TRY003, EM101

    return current_user


ActiveUser = Annotated[schemas.users.Read, Depends(get_active_user)]


async def get_creator_user(
    current_user: ActiveUser, uow: PostgresUOW, service: OrganizationUserService
) -> schemas.users.Read:
    org_user = await service.read_by_user_id(uow, current_user.id)
    if org_user.role != models.organization_user.UserRoles.CREATOR:
        raise core.services.exceptions.PermissionDeniedError("User is not creator")  # noqa: TRY003, EM101

    return current_user


CreatorUser = Annotated[schemas.users.Read, Depends(get_creator_user)]
