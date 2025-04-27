from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, TypeVar

from src.core.uow import UnitOfWork

ModelType = TypeVar("ModelType")


class BaseCRUD[ModelType](ABC):
    @abstractmethod
    async def create(self, uow: UnitOfWork, data: dict) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def create_many(self, uow: UnitOfWork, data_list: list[dict]) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def read_by_id(
        self,
        uow: UnitOfWork,
        entity_id: Any,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def read_many(
        self,
        uow: UnitOfWork,
        filters: dict | None = None,
        sorting: dict | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def update_by_id(
        self,
        uow: UnitOfWork,
        entity_id: Any,
        data: dict,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, uow: UnitOfWork, entity_id: Any) -> bool:
        raise NotImplementedError
