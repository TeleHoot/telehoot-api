from fastapi import APIRouter, HTTPException
from jose import jwt

from src import core
from src.app import auth
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])
settings = core.config.get_settings()


@router.post("/token")
def get_token(telegram_data: core.schemas.oauth.TelegramAuth, auth_service: dependencies.AuthService):

    return auth_service.auth_user(telegram_data)
