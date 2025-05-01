from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie

from src import core
from src.app import schemas, services
from src.core.config import get_settings
from src.core.uow import UnitOfWork

UsersService = Annotated[services.Users, Depends()]
OrganizationService = Annotated[services.Organizations, Depends()]
MembershipsService = Annotated[services.Memberships, Depends()]
QuestionsService = Annotated[services.Questions, Depends()]
QuizzesService = Annotated[services.Quizzes, Depends()]

PaginationQuery = Annotated[core.schemas.PaginationParams, Depends()]


settings = get_settings()


def get_uow_factory(
    *,
    use_postgres: bool = True,
    use_mongodb: bool = False,
) -> Callable[[], AsyncGenerator[UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[UnitOfWork]:
        async with UnitOfWork(use_postgres=use_postgres, use_mongodb=use_mongodb) as uow:
            yield uow

    return _get_uow


PostgresUOW = Annotated[UnitOfWork, Depends(get_uow_factory(use_postgres=True))]
MongoUOW = Annotated[UnitOfWork, Depends(get_uow_factory(use_mongodb=True))]
FullUOW = Annotated[UnitOfWork, Depends(get_uow_factory(use_postgres=True, use_mongodb=True))]

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
        raise core.services.exceptions.AuthenticationError("No session found")
    return await auth_service.read_user_by_token(uow, token)


CurrentUser = Annotated[schemas.users.Read, Depends(get_current_user)]


def get_active_user(current_user: CurrentUser) -> schemas.users.Read:
    if current_user.deleted_at is not None:
        raise core.services.exceptions.AuthenticationError("User is deleted")

    return current_user


ActiveUser = Annotated[schemas.users.Read, Depends(get_active_user)]


def get_admin_user(active_user: ActiveUser) -> schemas.users.Read:
    if not active_user.is_admin:
        raise core.services.exceptions.PermissionDeniedError("Admin permissions are required")

    return active_user


AdminUser = Annotated[schemas.users.Read, Depends(get_admin_user)]
