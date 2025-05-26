from fastapi import APIRouter, HTTPException, Request, Response

from src import core
from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


@router.post("/login/widget")
async def get_token_widget(
    telegram_data: schemas.users.TelegramAuth,
    uow: dependencies.uow.Postgres,
    auth_service: dependencies.services.Auth,
    response: Response,
):
    auth_data = await auth_service.auth_widget_user(uow, telegram_data)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=auth_data.access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.SESSION_EXPIRE_TIME,
    )

    return {"is_success": True}


@router.post("/login/tma")
async def get_token_tma(
    request: Request,
    uow: dependencies.uow.Postgres,
    auth_service: dependencies.services.Auth,
    response: Response,
):
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        raise HTTPException(status_code=400, detail="initData must be provided")

    auth_data = await auth_service.auth_tma_user(uow, init_data)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=auth_data.access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.SESSION_EXPIRE_TIME,
    )

    return {"is_success": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"is_success": True}
