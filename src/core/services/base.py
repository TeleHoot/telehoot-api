from typing import TypeVar, cast

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import logger, repositories, services

T = TypeVar("T", bound=BaseModel)
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

        data = self.prepare_data(create_schema.model_dump(exclude_unset=True))

        try:
            entity = await self.repo.create(session, data)
        except Exception as e:
            logger.service_logger.error(f"Error creating {self.create_schema.__name__}: {e!s}")
            raise services.exceptions.EntityCreateError(self.__class__.__name__, str(e)) from e

        logger.service_logger.info(f"Successfully created {self.create_schema.__name__}.")

        return cast(TRead, self.read_schema.model_validate(entity))

    @staticmethod
    def prepare_data(data: dict) -> dict:
        return data

    async def create_many(
        self,
        session: AsyncSession,
        create_schemas: list[TCreate],
    ) -> list[TRead]:
        logger.service_logger.info(f"Creating multiple {self.create_schema.__name__} entities.")

        data = [schema.model_dump(exclude_unset=True) for schema in create_schemas]

        try:
            entities = await self.repo.create_many(session, data)

        except Exception as e:
            logger.service_logger.error(f"Error creating entities: {e!s}")
            raise services.exceptions.EntityCreateError(self.__class__.__name__, str(e)) from e

        validated_entities: list[TRead] = [
            cast(TRead, self.read_schema.model_validate(entity)) for entity in entities
        ]

        logger.service_logger.info(f"Successfully created {len(entities)} entities.")
        return validated_entities

    async def read_by_id(self, session: AsyncSession, entity_id: int | str) -> TRead:
        logger.service_logger.info(f"Reading {self.read_schema.__name__} with ID: {entity_id}")

        try:
            entity = await self.repo.read_by_id(session, entity_id)

        except Exception as e:
            logger.service_logger.error(
                f"Error reading {self.read_schema.__name__} with ID {entity_id}: {e!s}",
            )
            raise services.exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        if not entity:
            logger.service_logger.error(f"Entity with ID {entity_id} not found.")
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        logger.service_logger.info(
            f"Successfully fetched {self.update_schema.__name__} with ID {entity_id}",
        )
        return cast(TRead, self.read_schema.model_validate(entity))

    async def read_all(self, session: AsyncSession, page: int = 1, limit: int = 10) -> list[TRead]:
        logger.service_logger.info(
            f"Reading all {self.read_schema.__name__} entities (Page: {page}, Limit: {limit})",
        )

        try:
            entities = await self.repo.read_all(session, page, limit)

        except Exception as e:
            logger.service_logger.error(f"Error reading all entities: {e!s}")
            raise services.exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        validated_entities = [cast(TRead, self.read_schema.model_validate(e)) for e in entities]

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

        try:
            updated_entity = await self.repo.update_by_id(session, entity_id, data)

            if not updated_entity:
                logger.service_logger.error(f"Entity with ID {entity_id} not found for update.")
                raise services.exceptions.EntityNotFoundError(  # noqa: TRY301
                    self.__class__.__name__,
                    f"entity_id: {entity_id}",
                )

        except Exception as e:
            logger.service_logger.error(f"Error updating entity with ID {entity_id}: {e!s}")
            raise services.exceptions.EntityUpdateError(self.__class__.__name__, str(e)) from e

        logger.service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}.",
        )
        return cast(TRead, self.read_schema.model_validate(updated_entity))

    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        logger.service_logger.info(f"Deleting {self.read_schema.__name__} with ID: {entity_id}")

        try:
            is_deleted = await self.repo.delete_by_id(session, entity_id)

        except Exception as e:
            logger.service_logger.error(f"Error deleting entity with ID {entity_id}: {e!s}")
            raise services.exceptions.EntityDeleteError(self.__class__.__name__, str(e)) from e

        if not is_deleted:
            logger.service_logger.error(f"Entity with ID {entity_id} not found for deletion.")
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"entity_id: {entity_id}",
            )

        logger.service_logger.info(f"Successfully deleted entity with ID {entity_id}.")
        return is_deleted
