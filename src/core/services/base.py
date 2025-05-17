import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from src.core import custom_types, repositories, schemas, services
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)
TFilters = TypeVar("TFilters", bound=schemas.BaseFilters)
TSorting = TypeVar("TSorting", bound=schemas.SortParams)
TModel = TypeVar("TModel")


class BaseCRUD[
    TCreate: BaseModel,
    TRead: BaseModel,
    TUpdate: BaseModel,
    TFilters: schemas.BaseFilters,
    TSorting: schemas.SortParams,
    TModel,
]:
    def __init__(
        self,
        repo: repositories.abstract.BaseCRUD[TModel],
        create_schema: type[TCreate],
        read_schema: type[TRead],
        update_schema: type[TUpdate],
        filters_schema: type[TFilters],
    ):
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.filters_schema = filters_schema
        self.context = {}
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    @log_operation
    async def create(
        self,
        uow: UnitOfWork,
        create_schema: TCreate,
        *,
        additional_data: dict[str, Any] | None = None,
    ) -> TRead:
        data = await self._dump_data(create_schema, additional_data)
        entity = await self.repo.create(uow, data)
        return await self._validate_data(entity)

    @log_operation
    async def create_many(
        self,
        uow: UnitOfWork,
        create_schemas: list[TCreate],
    ) -> list[TRead]:
        data = [await self._dump_data(schema) for schema in create_schemas]
        entities = await self.repo.create_many(uow, data)

        return [await self._validate_data(entity) for entity in entities]

    @log_operation
    async def read_by_id(
        self, uow: UnitOfWork, entity_id: custom_types.EntityID, *, include_deleted: bool = False
    ) -> TRead:
        entity = await self.repo.read_by_id(uow, entity_id, include_deleted=include_deleted)
        if not entity:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return await self._validate_data(entity)

    @log_operation
    async def read_many(
        self,
        uow: UnitOfWork,
        filters: TFilters | None = None,
        sorting: TSorting | None = None,
        pagination: schemas.PaginationParams | None = None,
        *,
        include_deleted: bool = False,
    ) -> list[TRead]:
        sorting_data = sorting.model_dump(exclude_none=True) if sorting else None
        filters_data = filters.model_dump(exclude_none=True) if filters else None

        page, limit = (pagination.page, pagination.limit) if pagination else (1, 10)

        entities = await self.repo.read_many(
            uow, filters_data, sorting_data, page, limit, include_deleted=include_deleted
        )

        return [await self._validate_data(entity) for entity in entities]

    @log_operation
    async def update_by_id(
        self,
        uow: UnitOfWork,
        entity_id: custom_types.EntityID,
        update_schema: TUpdate,
    ) -> TRead:
        data = await self._dump_data(update_schema)

        updated_entity = await self.repo.update_by_id(uow, entity_id, data)

        if not updated_entity:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return await self._validate_data(updated_entity)

    @log_operation
    async def delete_by_id(self, uow: UnitOfWork, entity_id: custom_types.EntityID) -> bool:
        is_deleted = await self.repo.delete_by_id(uow, entity_id)

        if not is_deleted:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return is_deleted

    async def _validate_data(self, entity: TModel) -> TRead:
        return self.read_schema.model_validate(entity)

    async def _dump_data(self, schema: BaseModel, additional_data: dict | None = None) -> dict:  # noqa: PLR6301
        dumped = schema.model_dump(exclude_unset=True)
        if additional_data:
            dumped.update(additional_data)
        return dumped
