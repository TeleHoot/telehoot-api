from typing import TypeVar, cast

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import exceptions, logger, models, repositories

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

    async def create(self, session: AsyncSession, create_schema: TCreate) -> TRead:
        logger.service_logger.info(f"Creating {self.create_schema.__name__} entity.")

        data = self._prepare_data(create_schema.model_dump(exclude_unset=True))

        entity = await self.repo.create(session, data)

        logger.service_logger.info(f"Successfully created {self.create_schema.__name__}.")

        return self._validate_data(entity)

    async def create_many(
        self,
        session: AsyncSession,
        create_schemas: list[TCreate],
    ) -> list[TRead]:
        logger.service_logger.info(f"Creating multiple {self.create_schema.__name__} entities.")

        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]

        entities = await self.repo.create_many(session, data)

        validated_entities: list[TRead] = [self._validate_data(entity) for entity in entities]

        logger.service_logger.info(f"Successfully created {len(entities)} entities.")
        return validated_entities

    async def read_by_id(self, session: AsyncSession, entity_id: int | str) -> TRead:
        logger.service_logger.info(f"Reading {self.read_schema.__name__} with ID: {entity_id}")

        entity = await self.repo.read_by_id(session, entity_id)

        if not entity:
            logger.service_logger.error(f"Entity with ID {entity_id} not found.")
            raise exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        logger.service_logger.info(
            f"Successfully fetched {self.update_schema.__name__} with ID {entity_id}",
        )
        return self._validate_data(entity)

    async def read_all(self, session: AsyncSession, page: int = 1, limit: int = 10) -> list[TRead]:
        logger.service_logger.info(
            f"Reading all {self.read_schema.__name__} entities (Page: {page}, Limit: {limit})",
        )
        limit = min(limit, 100)

        entities = await self.repo.read_all(session, page, limit)

        validated_entities = [self._validate_data(entity) for entity in entities]

        logger.service_logger.info(f"Successfully fetched {len(entities)} entities.")
        return validated_entities

    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        update_schema: TUpdate,
    ) -> TRead | None:
        logger.service_logger.info(f"Updating {self.update_schema.__name__} with ID: {entity_id}")

        data = update_schema.model_dump(exclude_unset=True)

        updated_entity = await self.repo.update_by_id(session, entity_id, data)

        if not updated_entity:
            logger.service_logger.error(f"Entity with ID {entity_id} not found for update.")
            raise exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        logger.service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}.",
        )
        return self._validate_data(updated_entity)

    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        logger.service_logger.info(f"Deleting {self.read_schema.__name__} with ID: {entity_id}")

        is_deleted = await self.repo.delete_by_id(session, entity_id)

        if not is_deleted:
            logger.service_logger.error(f"Entity with ID {entity_id} not found for deletion.")
            raise exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        logger.service_logger.info(f"Successfully deleted entity with ID {entity_id}.")
        return is_deleted

    @staticmethod
    def _prepare_data(data: dict) -> dict:
        return data

    def _validate_data(self, entity: models.Base) -> TRead:
        return cast(TRead, self.read_schema.model_validate(entity))
