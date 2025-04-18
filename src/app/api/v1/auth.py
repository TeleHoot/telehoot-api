from typing import Annotated, Doc, Optional

from jose import JWTError, jwt
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from src import core
from src.app import services, schemas
from src.app.api.v1 import dependencies

from fastapi.security import OAuth2
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class OAuth2Telegram(OAuth2):
    def __init__(
        self,
        scheme_name: Annotated[
            str | None,
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        scopes: Annotated[
            dict[str, str] | None,
            Doc(
                """
                The OAuth2 scopes that would be required by the *path operations* that
                use this dependency.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        *,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if no HTTP Authorization header is provided, required for
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """
            ),
        ] = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password=cast(Any, {"scopes": scopes}))
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

oauth2_scheme = OAuth2Telegram()

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, "BOT_SECRET", algorithms=["SHA256"])
    except JWTError as e:
        logger.error(f"Invalid authentication credentials: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

def get_current_user(uow: dependencies.UnitOfWork, users_service: dependencies.UsersService, token: str = Depends(oauth2_scheme)) -> schemas.users.Read:
    tg_data = decode_token(token)
    return users_service.read_by_tg_id(uow, tg_data.get("telegram_id"))
