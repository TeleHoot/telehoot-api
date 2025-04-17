from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeVar

from src.core import uow

ModelType = TypeVar("ModelType")


class BaseCRUD[ModelType](ABC):
    @abstractmethod
    async def create(self, uow: uow.UnitOfWork, data: dict) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def create_many(self, uow: uow.UnitOfWork, data_list: list[dict]) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def read_by_id(
        self,
        uow: uow.UnitOfWork,
        entity_id: int | str,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def read_many(
        self,
        uow: uow.UnitOfWork,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def update_by_id(
        self,
        uow: uow.UnitOfWork,
        entity_id: int | str,
        data: dict,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, uow: uow.UnitOfWork, entity_id: int | str) -> bool:
        raise NotImplementedError
