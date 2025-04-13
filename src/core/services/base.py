import logging
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import models, repositories, services
from src.core.utils.decorators import log_operation

TCreate = TypeVar("TCreate", bound=BaseModel)
TRead = TypeVar("TRead", bound=BaseModel)
TUpdate = TypeVar("TUpdate", bound=BaseModel)


class BaseCRUD[TCreate: BaseModel, TRead: BaseModel, TUpdate: BaseModel]:
    def __init__(
        self,
        repo: repositories.abstract.AbstractCRUD,
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
    async def create(self, session: AsyncSession, create_schema: TCreate) -> TRead:
        data = self._prepare_data(create_schema.model_dump(exclude_unset=True))
        entity = await self.repo.create(session, data)
        return self._validate_data(entity)

    @log_operation
    async def create_many(
        self,
        session: AsyncSession,
        create_schemas: list[TCreate],
    ) -> list[TRead]:
        data = [
            self._prepare_data(schema.model_dump(exclude_unset=True)) for schema in create_schemas
        ]
        entities = await self.repo.create_many(session, data)

        return [self._validate_data(e) for e in entities]

    @log_operation
    async def read_by_id(self, session: AsyncSession, entity_id: int | str) -> TRead:
        entity = await self.repo.read_by_id(session, entity_id)
        if not entity:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return self._validate_data(entity)

    @log_operation
    async def read_all(self, session: AsyncSession, page: int = 1, limit: int = 10) -> list[TRead]:
        entities = await self.repo.read_all(session, page, min(limit, 100))

        return [self._validate_data(e) for e in entities]

    @log_operation
    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        update_schema: TUpdate,
    ) -> TRead | None:
        data = update_schema.model_dump(exclude_unset=True)
        updated_entity = await self.repo.update_by_id(session, entity_id, data)

        if not updated_entity:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return self._validate_data(updated_entity)

    @log_operation
    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        is_deleted = await self.repo.delete_by_id(session, entity_id)
        if not is_deleted:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        return is_deleted

    @staticmethod
    def _prepare_data(data: dict) -> dict:
        return data

    def _validate_data(self, entity: models.Base) -> TRead:
        return self.read_schema.model_validate(entity)
