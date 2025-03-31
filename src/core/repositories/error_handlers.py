from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src.core import config, repositories

settings = config.get_settings()


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(repositories.exceptions.EntityCreateError)
    def handle_entity_create_error(
        request: Request, exc: repositories.exceptions.EntityCreateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(exc)
                if settings.DEBUG
                else "Database operation failed: cannot create entity",
                "error_code": "entity_create_failed",
            },
        )

    @app.exception_handler(repositories.exceptions.EntityReadError)
    def handle_entity_read_error(
        request: Request, exc: repositories.exceptions.EntityReadError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(exc)
                if settings.DEBUG
                else "Database operation failed: cannot read entity",
                "error_code": "entity_read_failed",
            },
        )

    @app.exception_handler(repositories.exceptions.EntityUpdateError)
    def handle_entity_update_error(
        request: Request, exc: repositories.exceptions.EntityUpdateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": str(exc)
                if settings.DEBUG
                else "Database operation failed: cannot update entity",
                "error_code": "entity_update_failed",
            },
        )

    @app.exception_handler(repositories.exceptions.EntityDeleteError)
    def handle_entity_delete_error(
        request: Request, exc: repositories.exceptions.EntityDeleteError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_423_LOCKED,  # Если удаление невозможно из-за блокировок
            content={
                "message": str(exc)
                if settings.DEBUG
                else "Database operation failed: cannot delete entity",
                "error_code": "entity_delete_failed",
            },
        )

    @app.exception_handler(repositories.exceptions.RepositoryError)
    def handle_repository_error(
        request: Request, exc: repositories.exceptions.RepositoryError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": str(exc) if settings.DEBUG else "Database operation failed",
                "error_code": "database_operation_failed",
            },
        )
