from fastapi import APIRouter

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()

@router.post("/token", response_model=schemas.auth.Token)
async def get_token(
    telegram_data: schemas.users.TelegramAuth,
    uow: dependencies.PostgresUOW,
    auth_service: dependencies.AuthService,
):
    return await auth_service.auth_user(uow, telegram_data)
