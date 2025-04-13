import logging
from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import models, repositories
from src.core.utils.decorators import log_operation

ModelType = TypeVar("ModelType", bound=models.Base)


class BaseCRUD(repositories.abstract.AbstractCRUD[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model
        self.logger = logging.getLogger(f"repositories.{model.__name__.lower()}")
        self.context = {
            "model": self.model.__name__,
            "table": self.model.__tablename__,
        }

    @log_operation
    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        try:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
        except IntegrityError as e:
            if "duplicate" in (err_info := str(e)):
                raise repositories.exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, err_info
                ) from e
            raise repositories.exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, err_info
            ) from e
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        return instance

    @log_operation
    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        try:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            for instance in instances:
                await session.refresh(instance)
        except IntegrityError as e:
            if "duplicate" in (err_info := str(e)):
                raise repositories.exceptions.DuplicateError(
                    self.__class__.__name__, self.model.__tablename__, err_info
                ) from e
            raise repositories.exceptions.EntityCreateError(
                self.__class__.__name__, self.model.__tablename__, err_info
            ) from e
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

        return instances

    @log_operation
    async def read_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
    ) -> ModelType | None:
        try:
            entity = await session.get(self.model, entity_id)
            if not entity:
                self.logger.info("Entity not found", extra={"exists": False})
            return entity
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @log_operation
    async def read_many(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        try:
            query = select(self.model)

            if issubclass(self.model, models.mixins.SoftDelete):
                query = query.where(self.model.deleted_at.is_(None))

            query = query.offset((page - 1) * limit).limit(limit)

            result = await session.scalars(query)
            return result.all()
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    @log_operation
    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        data: dict,
    ) -> ModelType | None:
        try:
            instance = await self.read_by_id(session, entity_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
            else:
                self.logger.warning("Update target not found", extra={"updated": False})
            return instance
        except Exception as e:
            raise repositories.exceptions.EntityUpdateError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e

    @log_operation
    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        try:
            instance = await self.read_by_id(session, entity_id)
            if not instance:
                self.logger.warning("Delete target not found", extra={"deleted": False})
                return False

            # Soft delete
            if issubclass(self.model, models.mixins.SoftDelete):
                if instance.deleted_at is None:
                    instance.deleted_at = func.timezone("UTC", func.now())
                    await session.flush()
                return True

            # Hard delete
            await session.delete(instance)
            await session.flush()
            return True

        except Exception as e:
            raise repositories.exceptions.EntityDeleteError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"entity_id: {entity_id}",
                str(e),
            ) from e
