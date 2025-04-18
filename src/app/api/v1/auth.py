from typing import Annotated, Doc, Optional

from jose import JWTError, jwt
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from src import core
from src.app import services, schemas
from src.app.api.v1 import dependencies

from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer()

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, "BOT_SECRET", algorithms=["SHA256"])
    except JWTError as e:
        logger.error(f"Invalid authentication credentials: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

def get_current_user(uow: dependencies.UnitOfWork, users_service: dependencies.UsersService, token: str = Depends(oauth2_scheme)) -> schemas.users.Read:
    tg_data = decode_token(token)
    return users_service.read_by_tg_id(uow, tg_data.get("telegram_id"))
