from src.core import custom_types


class ServiceError(Exception):
    """Base exception class for service errors."""


class EntityNotFoundError(ServiceError):
    """Raised when an entity cannot be found for a given operation, such as update or delete."""

    def __init__(self, service_name: str, identifier: custom_types.EntityID):
        super().__init__(
            f"{service_name} service failed to find entity with identifier ({identifier})"
        )


class PermissionDeniedError(ServiceError):  # 403
    """Raised when an action is forbidden for the user."""

    def __init__(self, message: str, service_name: str | None = None):
        msg = f"Forbidden. Detail: {message}" + (
            f" in {service_name} service" if service_name else ""
        )
        super().__init__(msg)


class AuthenticationError(ServiceError):  # 401
    """Invalid/missing credentials"""

    def __init__(self, message: str):
        super().__init__(f"Authentication failed. Detail: {message}")
