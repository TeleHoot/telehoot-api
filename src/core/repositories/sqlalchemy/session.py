from typing import List, Optional

from src.core.models.sqlalchemy.session import Session, SessionParticipant
from src.core.repositories.sqlalchemy import BaseCRUD
from src.core.uow import UnitOfWork


class SessionRepository(BaseCRUD[Session]):
    def __init__(self):
        super().__init__(Session)

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
            session_id=session_id,
            user_id=user_id,
            username=username
        )
        session.participants.append(participant)
        await uow.postgres_session.flush()
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

        for participant in session.participants:
            if participant.user_id == user_id:
                session.participants.remove(participant)
                await uow.postgres_session.flush()
                return True
        return False

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
                await uow.postgres_session.flush()
                return True
        return False 