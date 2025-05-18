from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.core.config import get_settings

from . import log_middleware

settings = get_settings()


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(log_middleware.LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not settings.DEBUG:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS)
