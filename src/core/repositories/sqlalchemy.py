import logging
from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import exceptions, models, repositories

ModelType = TypeVar("ModelType", bound=models.Base)


class BaseCRUD(repositories.abstract.Abstract[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model
        self.logger = logging.getLogger(f"repositories.{model.__name__.lower()}")

    def _base_context(self, operation: str) -> dict:
        return {
            "model": self.model.__name__,
            "table": self.model.__tablename__,
            "operation": operation,
        }

    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        context = self._base_context("create")
        self.logger.debug("Starting database operation", extra={**context, "data": data})

        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
        except IntegrityError as e:
            self.logger.exception("Database integrity error", extra={**context, "error": str(e)})
            if "duplicate" in (err_info := str(e)):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, err_info
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, err_info
            ) from e
        except Exception as e:
            self.logger.critical(
                "Unexpected database error", extra={**context, "error": str(e)}, exc_info=True
            )
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        self.logger.info(
            "Successfully created entity", extra={**context, "entity_id": instance.id}
        )
        return instance

    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        context = {**self._base_context("create_many"), "count": len(data_list)}
        self.logger.debug("Starting bulk create operation", extra=context)

        try:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
        except IntegrityError as e:
            self.logger.exception(
                "Bulk create integrity error", extra={**context, "error": str(e)}
            )
            if "duplicate" in repr(e):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, str(e)
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            ) from e
        except Exception as e:
            self.logger.critical(
                "Unexpected bulk create error", extra={**context, "error": str(e)}, exc_info=True
            )
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        self.logger.info(
            "Successfully created multiple entities",
            extra={**context, "created_count": len(instances)},
        )
        return instances

    async def read_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
    ) -> ModelType | None:
        context = {**self._base_context("read_by_id"), "entity_id": entity_id}
        self.logger.debug("Starting read operation", extra=context)

        try:
            entity = await session.get(self.model, entity_id)
            if entity:
                self.logger.info("Entity found", extra={**context, "exists": True})
            else:
                self.logger.info("Entity not found", extra={**context, "exists": False})
            return entity
        except Exception as e:
            self.logger.exception("Read operation failed", extra={**context, "error": str(e)})
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    async def read_all(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        context = {**self._base_context("read_all"), "page": page, "limit": limit}
        self.logger.debug("Starting read all operation", extra=context)

        try:
            result = await session.scalars(
                select(self.model).offset((page - 1) * limit).limit(limit),
            )
            entities = result.all()
            self.logger.info(
                "Read all operation completed", extra={**context, "result_count": len(entities)}
            )
            return entities
        except Exception as e:
            self.logger.exception("Read all operation failed", extra={**context, "error": str(e)})
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        data: dict,
    ) -> ModelType | None:
        context = {**self._base_context("update"), "entity_id": entity_id, "update_data": data}
        self.logger.debug("Starting update operation", extra={**context, "update_data": data})

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
                self.logger.info("Update operation successful", extra={**context, "updated": True})
            else:
                self.logger.warning("Update target not found", extra={**context, "updated": False})
            return instance
        except Exception as e:
            self.logger.exception("Update operation failed", extra={**context, "error": str(e)})
            raise exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        context = {**self._base_context("delete"), "entity_id": entity_id}
        self.logger.debug("Starting delete operation", extra=context)

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                await session.delete(instance)
                await session.flush()
                self.logger.info("Delete operation successful", extra={**context, "deleted": True})
                return True
            self.logger.warning("Delete target not found", extra={**context, "deleted": False})
            return False
        except Exception as e:
            self.logger.exception("Delete operation failed", extra={**context, "error": str(e)})
            raise exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e
