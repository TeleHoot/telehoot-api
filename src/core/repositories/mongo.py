import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TypeVar

from beanie import Document, SortDirection

from src.core import custom_types, repositories, schemas
from src.core.repositories import exceptions
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation

MongoModelType = TypeVar("MongoModelType", bound=Document)


class BaseCRUD(repositories.abstract.BaseCRUD[MongoModelType]):
    def __init__(self, model: type[MongoModelType]):
        self.model = model
        self.logger = logging.getLogger(f"repositories.{self.__class__.__name__.lower()}")
        self.context = {
            "model": self.model.__name__,
            "collection": self.model.get_collection_name(),
        }

    @log_operation
    async def create(self, uow: UnitOfWork, data: dict) -> MongoModelType:
        try:
            session = uow.mongo_session
            instance = self.model(**data)
            await instance.create(session=session)
            return instance
        except Exception as e:
            if "duplicate" in (err_info := str(e)):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.get_collection_name(), err_info
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.get_collection_name(), err_info
            ) from e

    @log_operation
    async def create_many(self, uow: UnitOfWork, data_list: list[dict]) -> list[MongoModelType]:
        try:
            session = uow.mongo_session
            instances = [self.model(**data) for data in data_list]
            await self.model.insert_many(instances, session=session)
            return instances
        except Exception as e:
            if "duplicate" in (err_info := str(e)):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.get_collection_name(), err_info
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.get_collection_name(), err_info
            ) from e

    @log_operation
    async def read_by_id(
        self,
        uow: UnitOfWork,
        entity_id: custom_types.EntityID,
    ) -> MongoModelType | None:
        try:
            session = uow.mongo_session
            entity = await self.model.get(entity_id, session=session)
            if not entity:
                self.logger.info("Entity not found", extra={"exists": False})
            return entity
        except Exception as e:
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @log_operation
    async def read_many(
        self,
        uow: UnitOfWork,
        filters: dict | None = None,
        sorting: dict | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[MongoModelType]:
        try:
            session = uow.mongo_session

            query_filters = filters or {}

            query = self.model.find(query_filters, session=session)

            if sorting and (sort_by := sorting.get("sort_by")) is not None:
                order_by = sorting.get("order_by", "asc")
                sort_direction = (
                    SortDirection.DESCENDING
                    if order_by == schemas.SortOrderField.DESCENDING
                    else SortDirection.ASCENDING
                )
                query = query.sort([(sort_by, sort_direction)])

            query = query.skip((page - 1) * limit).limit(limit)

            return await query.to_list()
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @log_operation
    async def update_by_id(
        self,
        uow: UnitOfWork,
        entity_id: custom_types.EntityID,
        data: dict,
    ) -> MongoModelType | None:
        try:
            session = uow.mongo_session
            instance = await self.read_by_id(uow, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await instance.save(session=session)
            else:
                self.logger.warning("Update target not found", extra={"updated": False})
            return instance
        except Exception as e:
            raise exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.model.get_collection_name(),
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    @log_operation
    async def delete_by_id(self, uow: UnitOfWork, entity_id: custom_types.EntityID) -> bool:
        try:
            session = uow.mongo_session
            instance = await self.read_by_id(uow, entity_id)
            if not instance:
                self.logger.warning("Delete target not found", extra={"deleted": False})
                return False

            # Soft delete (если модель поддерживает)
            if hasattr(instance, "deleted_at"):
                if instance.deleted_at is None:
                    instance.deleted_at = datetime.now(UTC)
                    await instance.save(session=session)
                return True

            # Hard delete
            await instance.delete(session=session)
            return True

        except Exception as e:
            raise exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.model.get_collection_name(),
                f"entity_id: {entity_id}",
                str(e),
            ) from e
