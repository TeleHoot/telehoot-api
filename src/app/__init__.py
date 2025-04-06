from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src import core
from src.app import api

settings = core.config.get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        default_response_class=ORJSONResponse,
    )

    core.middlewares.register_middlewares(app)

    core.error_handlers.register_error_handlers(app)

    app.include_router(api.v1.router, prefix=settings.API_PREFIX)

    return app
