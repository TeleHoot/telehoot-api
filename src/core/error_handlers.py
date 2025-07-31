from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src.core import config, repositories, services

settings = config.get_settings()


def make_error_response(
    message: str, user_message: str, error_code: str, http_status: int
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=http_status,
        content={
            "detail": message if settings.DEBUG else user_message,
            "error_code": error_code,
        },
    )


def register_error_handlers(app: FastAPI) -> None:  # noqa: C901
    @app.exception_handler(repositories.exceptions.EntityCreateError)
    def handle_entity_create_error(
        request: Request, exc: repositories.exceptions.EntityCreateError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc), "Failed to create resource", "create_failed", status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(repositories.exceptions.DuplicateError)
    def handle_duplicate_error(
        request: Request, exc: repositories.exceptions.DuplicateError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Failed to create resource: duplicate",
            "create_failed_duplicate",
            status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(repositories.exceptions.EntityReadError)
    def handle_entity_read_error(
        request: Request, exc: repositories.exceptions.EntityReadError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Failed to retrieve resource data",
            "read_failed",
            status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(repositories.exceptions.EntityUpdateError)
    def handle_entity_update_error(
        request: Request, exc: repositories.exceptions.EntityUpdateError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc), "Failed to update resource", "update_failed", status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(repositories.exceptions.EntityDeleteError)
    def handle_entity_delete_error(
        request: Request, exc: repositories.exceptions.EntityDeleteError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc), "Failed to delete resource", "delete_failed", status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(repositories.exceptions.DatabaseError)
    def handle_database_error(
        request: Request, exc: repositories.exceptions.DatabaseError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc), "Database error", "database_error", status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @app.exception_handler(services.exceptions.EntityNotFoundError)
    def handle_entity_not_found(
        request: Request, exc: services.exceptions.EntityNotFoundError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Requested resource not found",
            "resource_not_found",
            status.HTTP_404_NOT_FOUND,
        )

    @app.exception_handler(services.exceptions.PermissionDeniedError)
    def handle_permission_denied_error(
        request: Request, exc: services.exceptions.PermissionDeniedError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Access forbidden",
            "forbidden_access",
            status.HTTP_403_FORBIDDEN,
        )

    @app.exception_handler(services.exceptions.AuthenticationError)
    def handle_authentication_error(
        request: Request, exc: services.exceptions.AuthenticationError
    ) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Invalid/missing credentials",
            "authentication_failed",
            status.HTTP_401_UNAUTHORIZED,
        )

    @app.exception_handler(Exception)
    def handle_internal_server_error(request: Request, exc: Exception) -> ORJSONResponse:
        return make_error_response(
            str(exc),
            "Internal server error",
            "internal_error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
