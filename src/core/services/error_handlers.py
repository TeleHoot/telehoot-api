from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src.core import config, services

settings = config.get_settings()


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(services.exceptions.EntityNotFoundError)
    def handle_entity_not_found(
        request: Request, exc: services.exceptions.EntityNotFoundError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "message": str(exc) if settings.DEBUG else "Requested resource not found",
                "error_code": "resource_not_found",
            },
        )

    @app.exception_handler(services.exceptions.EntityCreateError)
    def handle_entity_create_error(
        request: Request, exc: services.exceptions.EntityCreateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(exc) if settings.DEBUG else "Cannot create resource",
                "error_code": "create_failed",
            },
        )

    @app.exception_handler(services.exceptions.EntityReadError)
    def handle_entity_read_error(
        request: Request, exc: services.exceptions.EntityReadError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(exc) if settings.DEBUG else "Failed to retrieve resource data",
                "error_code": "read_failed",
            },
        )

    @app.exception_handler(services.exceptions.EntityUpdateError)
    def handle_entity_update_error(
        request: Request, exc: services.exceptions.EntityUpdateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": str(exc) if settings.DEBUG else "Resource update conflict",
                "error_code": "update_conflict",
            },
        )

    @app.exception_handler(services.exceptions.EntityDeleteError)
    def handle_entity_delete_error(
        request: Request, exc: services.exceptions.EntityDeleteError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": str(exc) if settings.DEBUG else "Cannot delete resource",
                "error_code": "delete_failed",
            },
        )

    @app.exception_handler(services.exceptions.PermissionDeniedError)
    def handle_permission_denied_error(
        request: Request, exc: services.exceptions.PermissionDeniedError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": str(exc) if settings.DEBUG else "Access to this resource is forbidden",
                "error_code": "forbidden_access",
            },
        )

    @app.exception_handler(Exception)
    def handle_internal_server_error(request: Request, exc: Exception) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": str(exc) if settings.DEBUG else "Internal server error",
                "error_code": "internal_error",
            },
        )
