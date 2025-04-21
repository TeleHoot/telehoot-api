from fastapi import APIRouter

from src import core
from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


@router.post("/token")
def get_token(telegram_data: schemas.users.TelegramAuth, auth_service: dependencies.AuthService):
    return auth_service.auth_user(telegram_data)
