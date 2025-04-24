from fastapi import APIRouter, Response

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


@router.post("/login", response_model=bool)
async def get_token(
    telegram_data: schemas.users.TelegramAuth,
    uow: dependencies.PostgresUOW,
    auth_service: dependencies.AuthService,
    response: Response,
):
    auth_data = await auth_service.auth_user(uow, telegram_data)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=auth_data.access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="none" if not settings.DEBUG else "lax",
        max_age=settings.SESSION_EXPIRE_TIME,
    )

    return True


@router.post("/logout", response_model=bool)
async def logout(response: Response):
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return True


@router.get("/me")
async def get_me(current_user: dependencies.ActiveUser):
    return current_user
