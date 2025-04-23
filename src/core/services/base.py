import logging
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel

from src.core import repositories, services
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)
TModel = TypeVar("TModel")


class BaseCRUD[TCreate: BaseModel, TRead: BaseModel, TUpdate: BaseModel, TModel]:
    def __init__(
        self,
        repo: repositories.abstract.BaseCRUD[TModel],
        create_schema: type[TCreate],
        read_schema: type[TRead],
        update_schema: type[TUpdate],
    ):
        self.repo = repo
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.context = {}
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    @log_operation
    async def create(self, uow: UnitOfWork, create_schema: TCreate) -> TRead:
        data = await self._dump_data(create_schema)
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
    async def read_by_id(self, uow: UnitOfWork, entity_id: int | str | UUID) -> TRead:
        entity = await self.repo.read_by_id(uow, entity_id)
        if not entity:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return await self._validate_data(entity)

    @log_operation
    async def read_many(self, uow: UnitOfWork, page: int = 1, limit: int = 10) -> list[TRead]:
        entities = await self.repo.read_many(uow, page, min(limit, 100))

        return [await self._validate_data(entity) for entity in entities]

    @log_operation
    async def update_by_id(
        self,
        uow: UnitOfWork,
        entity_id: int | str | UUID,
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
    async def delete_by_id(self, uow: UnitOfWork, entity_id: int | str | UUID) -> bool:
        is_deleted = await self.repo.delete_by_id(uow, entity_id)

        if not is_deleted:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return is_deleted

    async def _validate_data(self, entity: TModel) -> TRead:
        return self.read_schema.model_validate(entity)

    @staticmethod
    async def _dump_data(schema: BaseModel) -> dict:
        return schema.model_dump(exclude_unset=True)
