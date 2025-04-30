import logging
from collections.abc import Sequence
from typing import Any, TypeVar

from beanie import Document, SortDirection

from src.core import custom_types, repositories, schemas
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
    async def create(self, uow: UnitOfWork, data: dict[str, Any]) -> MongoModelType:
        try:
            instance: MongoModelType = self.model(**data)
            await instance.create(session=uow.mongo_session)
            return instance
        except Exception as e:
            if "duplicate" in (err_info := str(e)):
                raise repositories.exceptions.DuplicateError(
                    self.__class__.__name__, self.model.get_collection_name(), err_info
                ) from e
            raise repositories.exceptions.EntityCreateError(
                self.__class__.__name__, self.model.get_collection_name(), err_info
            ) from e

    @log_operation
    async def create_many(
        self, uow: UnitOfWork, data_list: list[dict[str, Any]]
    ) -> list[MongoModelType]:
        try:
            instances = [self.model(**data) for data in data_list]
            await self.model.insert_many(instances, session=uow.mongo_session)
            return instances
        except Exception as e:
            if "duplicate" in (err_info := str(e)):
                raise repositories.exceptions.DuplicateError(
                    self.__class__.__name__, self.model.get_collection_name(), err_info
                ) from e
            raise repositories.exceptions.EntityCreateError(
                self.__class__.__name__, self.model.get_collection_name(), err_info
            ) from e

    @log_operation
    async def read_by_id(
        self,
        uow: UnitOfWork,
        entity_id: custom_types.EntityID,
    ) -> MongoModelType | None:
        try:
            entity = await self.model.get(entity_id, session=uow.mongo_session)
            if not entity:
                self.logger.info("Entity not found", extra={"exists": False})
            return entity
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @staticmethod
    def _process_filters(filters: dict[str, Any]) -> dict[str, Any]:
        """
        Returns:
            example output:
        {'created_at':
            {'$gte': datetime.datetime(2025, 1, 1, 0, 0),
            '$lte': datetime.datetime(2025, 5, 1, 0, 0)}}
        """
        processed = {}
        for key, value in filters.items():
            if key.endswith("_from"):
                field = key[:-5]
                operator = "$gte"
            elif key.endswith("_to"):
                field = key[:-3]
                operator = "$lte"
            else:
                processed[key] = value
                continue

            if field not in processed:
                processed[field] = {}
            processed[field][operator] = value
        return processed

    @staticmethod
    def _process_sort_param(sort: dict[str, Any] | None) -> list[tuple[str, SortDirection]] | None:
        return (
            (
                [
                    (
                        sort_by,
                        SortDirection.DESCENDING
                        if sort.get("order_by") == schemas.SortOrderField.DESCENDING
                        else SortDirection.ASCENDING,
                    )
                ]
                if (sort_by := sort.get("sort_by")) is not None
                else None
            )
            if sort
            else None
        )

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
            processed_filters = self._process_filters(filters or {})
            processed_sort_param = self._process_sort_param(sorting)

            skip = (page - 1) * limit

            return await self.model.find_many(
                processed_filters,
                session=uow.mongo_session,
                sort=processed_sort_param,
                skip=skip,
                limit=limit,
            ).to_list()

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
        data: dict[str, Any],
    ) -> MongoModelType | None:
        try:
            instance: MongoModelType = await self.read_by_id(uow, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await instance.save(session=uow.mongo_session)
            else:
                self.logger.warning("Update target not found", extra={"updated": False})
            return instance
        except Exception as e:
            raise repositories.exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.model.get_collection_name(),
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    @log_operation
    async def delete_by_id(self, uow: UnitOfWork, entity_id: custom_types.EntityID) -> bool:
        try:
            instance = await self.read_by_id(uow, entity_id)
            if not instance:
                self.logger.warning("Delete target not found", extra={"deleted": False})
                return False

            # soft deletes document if it is an instance of DocumentWithSoftDelete,
            # otherwise hard deletes
            await instance.delete(session=uow.mongo_session)

            return True

        except Exception as e:
            raise repositories.exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.model.get_collection_name(),
                f"entity_id: {entity_id}",
                str(e),
            ) from e
