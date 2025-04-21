from fastapi import APIRouter

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


@router.post("/token")
async def get_token(
    telegram_data: schemas.users.TelegramAuth,
    uow: dependencies.PostgresUOW,
    auth_service: dependencies.AuthService,
):
    token = await auth_service.auth_user(uow, telegram_data)
    return {"access_token": token, "token_type": "bearer"}
