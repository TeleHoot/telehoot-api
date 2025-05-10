from typing import Annotated

from fastapi import Depends, WebSocket, status
from fastapi.security import APIKeyCookie

from src import core
from src.app import schemas
from src.app.api.dependencies import services, uow

settings = core.config.get_settings()

cookie = APIKeyCookie(
    name=settings.SESSION_COOKIE_NAME,
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str, Depends(cookie)],
    uow: uow.Postgres,
    auth_service: services.Auth,
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


async def get_ws_user(
    websocket: WebSocket,
    uow: uow.Postgres,
    auth_service: services.Auth,
) -> schemas.users.Read:
    token = websocket.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise core.services.exceptions.AuthenticationError("No session found")
    return await auth_service.read_user_by_token(uow, token)


WsUser = Annotated[schemas.users.Read, Depends(get_ws_user)]
