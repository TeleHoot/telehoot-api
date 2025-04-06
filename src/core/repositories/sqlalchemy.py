from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import exceptions, logger, models, repositories

ModelType = TypeVar("ModelType", bound=models.Base)


class BaseCRUD(repositories.abstract.Abstract[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        logger.repository_logger.info(f"Creating a new {self.model.__name__}: {data}")
        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
        except IntegrityError as e:
            logger.repository_logger.error(
                f"Constraint violation creating {self.model.__name__}, data {data}. Error: {e}",
                exc_info=True,
            )
            if "duplicate" in (err_info := str(e)):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, err_info
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, err_info
            ) from e
        except Exception as e:
            logger.repository_logger.critical(
                f"Database error: {e}",
                exc_info=True,
            )
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        logger.repository_logger.info(f"Successfully created {self.model.__name__}: {instance}")
        return instance

    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        logger.repository_logger.info(f"Creating multiple {self.model.__name__} entities")
        try:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
        except IntegrityError as e:
            if "duplicate" in repr(e):
                raise exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, str(e)
                ) from e
            raise exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, str(e)
            ) from e
        except Exception as e:
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
        logger.repository_logger.info(
            f"Successfully created multiple {self.model.__name__} entities",
        )
        return instances

    async def read_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
    ) -> ModelType | None:
        logger.repository_logger.info(f"Fetching {self.model.__name__} by ID: {entity_id}")

        try:
            entity = await session.get(self.model, entity_id)
        except Exception as e:
            logger.repository_logger.critical(
                f"Database error: {e}",
                exc_info=True,
            )
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        if entity:
            logger.repository_logger.info(f"Found {self.model.__name__} with ID: {entity_id}")
        else:
            logger.repository_logger.warning(
                f"No {self.model.__name__} found with ID: {entity_id}"
            )

        return entity

    async def read_all(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        logger.repository_logger.info(
            f"Fetching all {self.model.__name__} entities. Page: {page}, Limit: {limit}",
        )

        try:
            result = await session.scalars(
                select(self.model).offset((page - 1) * limit).limit(limit),
            )
            entities = result.all()
        except Exception as e:
            logger.repository_logger.critical(
                f"Database error: {e}",
                exc_info=True,
            )
            raise exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        logger.repository_logger.info(f"Fetched {len(entities)} {self.model.__name__} entities")
        return entities

    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        data: dict,
    ) -> ModelType | None:
        logger.repository_logger.info(
            f"Updating {self.model.__name__} with ID: {entity_id}, Data: {data}",
        )

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
        except Exception as e:
            logger.repository_logger.error(
                f"Error updating {self.model.__name__} with ID: {entity_id}, Error: {e}",
                exc_info=True,
            )
            raise exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

        if instance:
            logger.repository_logger.info(
                f"Successfully updated {self.model.__name__} with ID: {entity_id}",
            )
        else:
            logger.repository_logger.warning(
                f"No {self.model.__name__} updated for ID: {entity_id}",
            )
        return instance

    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        logger.repository_logger.info(f"Deleting {self.model.__name__} with ID: {entity_id}")

        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                await session.delete(instance)
                await session.flush()
                return True
            return False
        except Exception as e:
            logger.repository_logger.error(
                f"Error deleting {self.model.__name__} with ID: {entity_id}, Error: {e}",
                exc_info=True,
            )
            raise exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e
