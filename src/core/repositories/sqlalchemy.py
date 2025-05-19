import logging
from collections.abc import Sequence
from typing import Any, ClassVar, TypeVar

from sqlalchemy import Select, and_, func, inspect, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute

from src.core import custom_types, models, repositories, schemas
from src.core.uow import UnitOfWork
from src.core.utils.decorators import log_operation

SQLModelType = TypeVar("SQLModelType", bound=models.sqlalchemy.Base)


class BaseCRUD(repositories.abstract.BaseCRUD[SQLModelType]):
    def __init__(self, model: type[SQLModelType]):
        self.model = model
        self.logger = logging.getLogger(f"repositories.{self.__class__.__name__.lower()}")
        self.context = {
            "model": self.model.__name__,
        }

    search_fields: ClassVar[list[InstrumentedAttribute]] = []

    @log_operation
    async def create(self, uow: UnitOfWork, data: dict) -> SQLModelType:
        try:
            session = uow.postgres_session
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
    async def create_many(self, uow: UnitOfWork, data_list: list[dict]) -> list[SQLModelType]:
        try:
            session = uow.postgres_session
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
        self, uow: UnitOfWork, entity_id: custom_types.EntityID, *, include_deleted: bool = False
    ) -> SQLModelType | None:
        try:
            session = uow.postgres_session
            query = select(self.model)

            pk_columns: tuple = inspect(self.model).primary_key

            if isinstance(entity_id, dict):
                for column in pk_columns:
                    query = query.where(column == entity_id[column.name])
            else:
                query = query.where(pk_columns[0] == entity_id)

            if not include_deleted and issubclass(self.model, models.sqlalchemy.SoftDelete):
                query = query.where(self.model.deleted_at.is_(None))

            return await session.scalar(query)
        except Exception as e:
            raise repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e

    def _process_filters(self, query: Select, filters: dict[str, Any]) -> Select:
        for field, value in filters.items():
            if value is None:
                continue
            if field.endswith("_from"):
                field_name = field[:-5]
                column = getattr(self.model, field_name)
                query = query.where(column >= value)
            elif field.endswith("_to"):
                field_name = field[:-3]
                column = getattr(self.model, field_name)
                query = query.where(column <= value)
            elif field == "search":
                if not self.search_fields:
                    self.logger.error(
                        "Search query given but no search fields defined for the model"
                    )
                    continue

                search_terms = value.strip().split()

                conditions = [
                    or_(*[search_field.ilike(f"%{term}%") for search_field in self.search_fields])
                    for term in search_terms
                ]
                # there should be at least one field matching every term. Example:
                # search_terms = ["brainrot","quiz"], search_fields = [name,description]
                # ("brainrot" in name OR "brainrot" in description)
                # AND
                # ("quiz" in name OR "quiz" in description)
                query = query.where(and_(*conditions))
            else:
                column = getattr(self.model, field)
                if isinstance(value, list):
                    query = query.where(column.in_(value))
                else:
                    query = query.where(column == value)
        return query

    @log_operation
    async def read_many(
        self,
        uow: UnitOfWork,
        filters: dict | None = None,
        sorting: dict | None = None,
        page: int = 1,
        limit: int = 10,
        *,
        include_deleted: bool = False,
    ) -> Sequence[SQLModelType]:
        try:
            session = uow.postgres_session

            query = select(self.model)

            if not include_deleted and issubclass(self.model, models.sqlalchemy.SoftDelete):
                query = query.where(self.model.deleted_at.is_(None))

            if filters:
                query = self._process_filters(query, filters)

            if sorting and (sort_by := sorting.get("sort_by")) is not None:
                order_by = sorting.get("order_by", "asc")
                column = getattr(self.model, sort_by)
                query = query.order_by(
                    column.desc()
                    if order_by == schemas.SortOrderField.DESCENDING
                    else column.asc()
                )

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
        uow: UnitOfWork,
        entity_id: custom_types.EntityID,
        data: dict,
    ) -> SQLModelType | None:
        try:
            session = uow.postgres_session
            instance = await self.read_by_id(uow, entity_id)
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
    async def delete_by_id(self, uow: UnitOfWork, entity_id: custom_types.EntityID) -> bool:
        try:
            session = uow.postgres_session
            instance = await self.read_by_id(uow, entity_id)
            if not instance:
                self.logger.warning("Delete target not found", extra={"deleted": False})
                return False

            if issubclass(self.model, models.sqlalchemy.SoftDelete):
                if instance.deleted_at is None:
                    instance.deleted_at = func.timezone("UTC", func.now())
                    await session.flush()

                    await self._soft_delete_cascades(uow, instance)
                return True

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

    async def _soft_delete_cascades(self, uow: UnitOfWork, instance: SQLModelType) -> None:
        """Cascading soft deletes. Examples are with Organizations and Quizzes."""

        if not hasattr(self.model, "__soft_delete_cascades__"):
            return

        for relation_name in self.model.__soft_delete_cascades__:  # type: ignore[attr-defined]
            # Organization.quizzes
            relation = getattr(self.model, relation_name)

            # <class 'src.app.models.quiz.Quiz'>
            target_cls = relation.mapper.class_

            # quizzes.id, quizzes.organization_id, quizzes.author_id, quizzes.name etc.
            rel_table_cols = relation.mapper.columns

            # Construct cascade conditions (WHERE quizzes.organization_id = .......)
            # Also filter out unnecessary foreign keys
            # For Quiz model there are organization_id (target) and author_id (not needed)
            conditions = [
                col == getattr(instance, fk.column.name)
                for col in rel_table_cols
                if col.foreign_keys
                for fk in col.foreign_keys
                if fk.column.table.name == instance.__tablename__
            ]

            if conditions and issubclass(target_cls, models.sqlalchemy.SoftDelete):
                stmt = (
                    update(target_cls)
                    .where(*conditions)
                    .values(deleted_at=func.timezone("UTC", func.now()))
                )
                await uow.postgres_session.execute(stmt)
