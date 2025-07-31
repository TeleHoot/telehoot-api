from src.core import custom_types


class RepositoryError(Exception):
    """Base exception class for repository errors."""


class DatabaseError(RepositoryError):
    """Raised when there is a database error."""

    def __init__(self, repo_name: str, message: str):
        super().__init__(f"Database error in {repo_name} repository. Detail: {message}")


class EntityCreateError(RepositoryError):
    """Raised when an entity cannot be created."""

    def __init__(self, repo_name: str, table_name: str, message: str):
        super().__init__(
            f"{repo_name} repository failed to create entity in '{table_name}'. Detail: {message}"
        )


class DuplicateError(RepositoryError):
    """Raised when a unique constraint is violated."""

    def __init__(self, repo_name: str, table_name: str, message: str):
        super().__init__(
            f"Duplicate entry in {repo_name} repository, table '{table_name}'. Detail: {message}"
        )


class EntityReadError(RepositoryError):
    """Raised when an entity cannot be read."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: custom_types.EntityID,
        message: str,
    ):
        super().__init__(
            f"{repo_name} repository failed to read entity from '{table_name}' "
            f"with ID: {identifier}. Detail: {message}",
        )


class EntityUpdateError(RepositoryError):
    """Raised when an entity cannot be updated."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: custom_types.EntityID,
        message: str,
    ):
        super().__init__(
            f"{repo_name} repository failed to update entity in '{table_name}' "
            f"with ID: {identifier}. Detail: {message}",
        )


class EntityDeleteError(RepositoryError):
    """Raised when an entity cannot be deleted."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: custom_types.EntityID,
        message: str,
    ):
        super().__init__(
            f"{repo_name} repository failed to delete entity in '{table_name}' "
            f"with ID: {identifier}. Detail: {message}",
        )
