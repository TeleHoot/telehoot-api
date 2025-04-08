import logging
from typing import TypeVar, cast

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import exceptions, models, repositories

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class BaseCRUD[TCreate: BaseModel, TRead: BaseModel, TUpdate: BaseModel]:
    def __init__(
        self,
        repo: repositories.sqlalchemy.BaseCRUD,
        create_schema: type[TCreate],
        read_schema: type[TRead],
        update_schema: type[TUpdate],
    ):
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    async def create(self, session: AsyncSession, create_schema: TCreate) -> TRead:
        context = {"operation": "create"}
        self.logger.debug(
            "Starting entity creation", extra={**context, "input_data": create_schema.model_dump()}
        )

        try:
            data = self._prepare_data(create_schema.model_dump(exclude_unset=True))
            entity = await self.repo.create(session, data)
            validated = self._validate_data(entity)

            self.logger.info(
                "Entity created successfully",
                extra={**context, "entity_id": getattr(entity, "id", None)},
            )
            return validated
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Entity creation failed",
                extra={**context, "error": str(e)},
            )
            raise exceptions.EntityCreateError(
                self.__class__.__name__,
                self.create_schema.__name__,
                str(e),
            ) from e

    async def create_many(
        self,
        session: AsyncSession,
        create_schemas: list[TCreate],
    ) -> list[TRead]:
        context = {"operation": "create_many", "count": len(create_schemas)}
        self.logger.debug("Starting bulk entity creation", extra=context)

        try:
            data = [
                self._prepare_data(schema.model_dump(exclude_unset=True))
                for schema in create_schemas
            ]
            entities = await self.repo.create_many(session, data)
            validated_entities = [self._validate_data(e) for e in entities]

            self.logger.info(
                "Bulk creation completed", extra={**context, "created_count": len(entities)}
            )
            return validated_entities
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Bulk creation failed",
                extra={**context, "error": str(e)},
            )
            raise exceptions.EntityCreateError(
                self.__class__.__name__,
                self.create_schema.__name__,
                str(e),
            ) from e

    async def read_by_id(self, session: AsyncSession, entity_id: int | str) -> TRead:
        context = {"operation": "read_by_id", "entity_id": entity_id}
        self.logger.debug("Fetching entity by ID", extra=context)

        try:
            entity = await self.repo.read_by_id(session, entity_id)
            if not entity:
                self.logger.warning("Entity not found", extra={**context, "exists": False})
                raise exceptions.EntityNotFoundError(
                    self.__class__.__name__,
                    f"entity_id: {entity_id}",
                )

            self.logger.info("Entity retrieved successfully", extra={**context, "exists": True})
            return self._validate_data(entity)
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Entity retrieval failed",
                extra={**context, "error": str(e)},
            )
            raise

    async def read_all(self, session: AsyncSession, page: int = 1, limit: int = 10) -> list[TRead]:
        context = {"operation": "read_all", "page": page, "limit": limit}
        self.logger.debug("Fetching paginated entities", extra=context)

        try:
            entities = await self.repo.read_all(session, page, min(limit, 100))
            self.logger.info(
                "Paginated fetch completed", extra={**context, "result_count": len(entities)}
            )
            return [self._validate_data(e) for e in entities]
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Paginated fetch failed",
                extra={**context, "error": str(e)},
            )
            raise

    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        update_schema: TUpdate,
    ) -> TRead | None:
        context = {
            "operation": "update_by_id",
            "entity_id": entity_id,
        }
        self.logger.debug(
            "Starting entity update", extra={**context, "update_data": update_schema.model_dump()}
        )

        try:
            data = update_schema.model_dump(exclude_unset=True)
            updated_entity = await self.repo.update_by_id(session, entity_id, data)

            if not updated_entity:
                self.logger.warning("Update target not found", extra={**context, "updated": False})
                raise exceptions.EntityNotFoundError(
                    self.__class__.__name__,
                    f"entity_id: {entity_id}",
                )

            self.logger.info("Entity updated successfully", extra={**context, "updated": True})
            return self._validate_data(updated_entity)
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Entity update failed",
                extra={**context, "error": str(e)},
            )
            raise exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.update_schema.__name__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        context = {"operation": "delete_by_id", "entity_id": entity_id}
        self.logger.debug("Starting entity deletion", extra=context)

        try:
            is_deleted = await self.repo.delete_by_id(session, entity_id)
            if not is_deleted:
                self.logger.warning("Delete target not found", extra={**context, "deleted": False})
                raise exceptions.EntityNotFoundError(
                    self.__class__.__name__,
                    f"entity_id: {entity_id}",
                )

            self.logger.info("Entity deleted successfully", extra={**context, "deleted": True})
            return is_deleted
        except exceptions.DatabaseError as e:
            self.logger.exception(
                "Entity deletion failed",
                extra={**context, "error": str(e)},
            )
            raise exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.read_schema.__name__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    @staticmethod
    def _prepare_data(data: dict) -> dict:
        return data

    def _validate_data(self, entity: models.Base) -> TRead:
        return cast(TRead, self.read_schema.model_validate(entity))
