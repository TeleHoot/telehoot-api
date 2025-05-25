import logging.config
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src import core
from src.app import api
from src.app.api.v1 import ws_handlers as ws_handlers  # noqa: PLC0414
from src.app.models import gather_documents

settings = core.config.get_settings()
ws_manager = core.websockets.get_websocket_manager()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        core.db.init_replica_set()
        await core.db.init_mongo(gather_documents)
        await ws_manager.connect_to_redis()
        yield
        await ws_manager.disconnect_from_redis()
        if mongo_client := core.db.get_mongo_manager().client:
            mongo_client.close()

    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    logging.config.dictConfig(core.logger.setup_logger())

    core.middlewares.register_middlewares(app)

    core.error_handlers.register_error_handlers(app)

    app.include_router(api.v1.router, prefix=settings.API_PREFIX)

    return app
