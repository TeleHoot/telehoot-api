from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.config import get_settings

settings = get_settings()


def add_middlewares(application: FastAPI) -> None:
    """
    Adds necessary middleware components to the FastAPI application.
    """
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not settings.DEBUG:
        application.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS
        )


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance, setting up
    resources, middlewares, and routing.
    """

    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return app
