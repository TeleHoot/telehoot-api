from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class Abstract[ModelType](ABC):
    @abstractmethod
    async def create(self, session: AsyncSession, data: dict) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def create_many(self, session: AsyncSession, data_list: list[dict]) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def read_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def read_all(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def update_by_id(
        self,
        session: AsyncSession,
        entity_id: int | str,
        data: dict,
    ) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, session: AsyncSession, entity_id: int | str) -> bool:
        raise NotImplementedError
