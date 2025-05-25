from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, WebSocket, status
from fastapi.security import APIKeyCookie

from src import core
from src.app import models, schemas
from src.app.api.dependencies import services, uow

settings = core.config.get_settings()

cookie = APIKeyCookie(
    name=settings.SESSION_COOKIE_NAME,
    auto_error=False,
)


async def get_optional_user(
    token: Annotated[str | None, Depends(cookie)],
    uow: uow.Postgres,
    auth_service: services.Auth,
) -> schemas.users.Read | None:
    if token:
        return await auth_service.read_user_by_token(uow, token)
    return None


OptionalUser = Annotated[schemas.users.Read | None, Depends(get_optional_user)]


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


def require_org_role(*allowed_roles: models.UserRoles) -> Callable:
    async def dependency(
        organization_id: UUID,
        uow: uow.Postgres,
        memberships_service: services.Memberships,
        current_user: ActiveUser,
    ) -> schemas.users.Read:
        membership = await memberships_service.read_by_id(
            uow, entity_id={"organization_id": organization_id, "user_id": current_user.id}
        )
        if membership.role not in allowed_roles:
            raise core.services.exceptions.PermissionDeniedError(
                f"Roles required: {', '.join(allowed_roles)}. Your role: {membership.role}."
            )
        return current_user

    return dependency


get_org_owner = require_org_role(models.UserRoles.OWNER)
get_org_editor = require_org_role(models.UserRoles.OWNER, models.UserRoles.EDITOR)
get_org_presenter = require_org_role(
    models.UserRoles.OWNER, models.UserRoles.EDITOR, models.UserRoles.PRESENTER
)

OrganizationOwner = Annotated[schemas.users.Read, Depends(get_org_owner)]
OrganizationEditor = Annotated[schemas.users.Read, Depends(get_org_editor)]
OrganizationPresenter = Annotated[schemas.users.Read, Depends(get_org_presenter)]
