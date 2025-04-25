from fastapi import HTTPException
from src.core.repositories.mongo.session import SessionRepository
from src.core.schemas.session import SessionCreate, SessionRead, SessionUpdate
from src.core.services.base import BaseCRUD
from src.core.uow import UnitOfWork


class SessionsService(BaseCRUD[SessionCreate, SessionRead, SessionUpdate, SessionRepository]):
    def __init__(self):
        super().__init__(
            repo=SessionRepository(),
            create_schema=SessionCreate,
            read_schema=SessionRead,
            update_schema=SessionUpdate
        )

    async def add_participant(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str,
        username: str
    ) -> SessionRead:
        """Добавление участника в сессию"""
        participant = await self.add_participant(uow, session_id, user_id, username)
        if not participant:
            raise HTTPException(status_code=404, detail="Session not found")
        return await self.read_by_id(uow, session_id)

    async def remove_participant(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str
    ) -> SessionRead:
        """Удаление участника из сессии"""
        if not await self.remove_participant(uow, session_id, user_id):
            raise HTTPException(status_code=404, detail="Session or participant not found")
        return await self.read_by_id(uow, session_id)

    async def update_participant_score(
        self,
        uow: UnitOfWork,
        session_id: str,
        user_id: str,
        score: int
    ) -> SessionRead:
        """Обновление счета участника"""
        if not await self.update_participant_score(uow, session_id, user_id, score):
            raise HTTPException(status_code=404, detail="Session or participant not found")
        return await self.read_by_id(uow, session_id)

    async def start_session(self, uow: UnitOfWork, session_id: str) -> SessionRead:
        """Начало сессии"""
        return await self.update_by_id(
            uow,
            session_id,
            SessionUpdate(status="in_progress")
        )

    async def end_session(self, uow: UnitOfWork, session_id: str) -> SessionRead:
        """Завершение сессии"""
        return await self.update_by_id(
            uow,
            session_id,
            SessionUpdate(status="completed")
        )


sessions_service = SessionsService() 