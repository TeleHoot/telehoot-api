from typing import Dict, Optional
from src.core.stats.handlers import SessionStatsHandler


class StatsManager:
    def __init__(self):
        self.sessions: Dict[str, SessionStatsHandler] = {}

    def create_session(self, session_id: str) -> SessionStatsHandler:
        self.sessions[session_id] = SessionStatsHandler(session_id)
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[SessionStatsHandler]:
        return self.sessions.get(session_id)

    def end_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].end_session()
            # TODO: Добавить сохранение статистики в базу данных
            del self.sessions[session_id]


# Глобальный менеджер статистики
stats_manager = StatsManager() 