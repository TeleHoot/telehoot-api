import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt

from src.app import schemas
from src.app.api.v1 import dependencies
from src.core.config import get_settings
from src.core.uow import UnitOfWork

settings = get_settings()

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="todo", tokenUrl="todo")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.TG.BOT_SECRET, algorithms=[settings.TG.ALGORITHM])
    except JWTError as e:
        logger.exception("Invalid authentication credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
        ) from e


def get_current_user(
    uow: UnitOfWork,
    users_service: dependencies.UsersService,
    token: str = Depends(oauth2_scheme),
) -> schemas.users.Read:
    tg_data = decode_token(token)
    return users_service.read_by_tg_id(uow, tg_data.get("id"))
