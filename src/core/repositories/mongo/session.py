from typing import List, Optional
from uuid import uuid4

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession

from src.app.models.session import Session, SessionParticipant
from src.core.repositories.abstract import BaseCRUD
from src.core.uow import UnitOfWork


class SessionRepository(BaseCRUD[Session]):
    def __init__(self):
        self.model = Session

    async def create(self, uow: UnitOfWork, data: dict) -> Session:
        # Генерируем ID для новой сессии
        data["_id"] = str(uuid4())
        session = Session(**data)
        await session.insert(session=uow.mongo_session)
        return session

    async def create_many(self, uow: UnitOfWork, data_list: List[dict]) -> List[Session]:
        # Генерируем ID для каждой сессии
        for data in data_list:
            data["_id"] = str(uuid4())
        sessions = [Session(**data) for data in data_list]
        await Session.insert_many(sessions, session=uow.mongo_session)
        return sessions

    async def read_by_id(self, uow: UnitOfWork, entity_id: str) -> Optional[Session]:
        try:
            # Пробуем преобразовать в ObjectId
            object_id = PydanticObjectId(entity_id)
            return await Session.get(object_id, session=uow.mongo_session)
        except Exception:
            # Если не получилось, ищем по строковому ID
            return await Session.find_one({"id": entity_id}, session=uow.mongo_session)

    async def read_many(
        self, uow: UnitOfWork, page: int = 1, limit: int = 10, filters: dict | None = None
    ) -> List[Session]:
        query = {}
        if filters:
            query.update(filters)
            
        return await Session.find(
            query,
            skip=(page - 1) * limit,
            limit=limit,
            session=uow.mongo_session
        ).to_list()

    async def update_by_id(
        self, uow: UnitOfWork, entity_id: str, data: dict
    ) -> Optional[Session]:
        session = await self.read_by_id(uow, entity_id)
        if session:
            for key, value in data.items():
                setattr(session, key, value)
            await session.save(session=uow.mongo_session)
        return session

    async def delete_by_id(self, uow: UnitOfWork, entity_id: str) -> bool:
        session = await self.read_by_id(uow, entity_id)
        if session:
            await session.delete(session=uow.mongo_session)
            return True
        return False

    async def add_participant(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str,
        username: str
    ) -> Optional[SessionParticipant]:
        """Добавление участника в сессию"""
        session = await self.read_by_id(uow, session_id)
        if not session:
            return None

        participant = SessionParticipant(
            user_id=user_id,
            username=username
        )
        session.participants.append(participant)
        await session.save(session=uow.mongo_session)
        return participant

    async def remove_participant(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str
    ) -> bool:
        """Удаление участника из сессии"""
        session = await self.read_by_id(uow, session_id)
        if not session:
            return False

        session.participants = [
            p for p in session.participants if p.user_id != user_id
        ]
        await session.save(session=uow.mongo_session)
        return True

    async def update_participant_score(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str,
        score: int
    ) -> bool:
        """Обновление счета участника"""
        session = await self.read_by_id(uow, session_id)
        if not session:
            return False

        for participant in session.participants:
            if participant.user_id == user_id:
                participant.score = score
                await session.save(session=uow.mongo_session)
                return True
        return False 