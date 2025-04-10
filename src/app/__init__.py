import logging.config

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src import core
from src.app import api
from src.app.models import gather_documents

settings = core.config.get_settings()


def create_app() -> FastAPI:
    async def lifespan(application: FastAPI):
        await core.db.init_mongo(settings, gather_documents)
        yield

    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,  # type: ignore[valid-type]
    )

    logging.config.dictConfig(core.logger.setup_logger())

    core.middlewares.register_middlewares(app)

    core.error_handlers.register_error_handlers(app)

    app.include_router(api.v1.router, prefix=settings.API_PREFIX)

    return app
