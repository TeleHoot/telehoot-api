from fastapi import WebSocket
from src.core.websocket import Event, EventType, SessionRole
from src.core.stats.manager import stats_manager
from src.core.stats.models import AnswerStats
from src.app.models import User


class SessionEventHandler:
    def __init__(self, session_id: str, current_user: User, role: SessionRole):
        self.session_id = session_id
        self.current_user = current_user
        self.role = role
        self.stats = stats_manager.get_session(session_id)
        if not self.stats:
            self.stats = stats_manager.create_session(session_id)

    def create_event(self, type: EventType, data: dict) -> Event:
        return Event(type=type, session_id=self.session_id, data=data)

    async def handle_join(self, websocket: WebSocket) -> Event:
        """Обработка подключения нового участника"""
        self.stats.add_participant(
            str(self.current_user.id),
            self.current_user.telegram_username
        )
        
        return self.create_event(
            EventType.JOIN,
            {
                "user_id": str(self.current_user.id),
                "username": self.current_user.telegram_username,
                "role": self.role
            }
        )

    async def handle_leave(self) -> Event:
        """Обработка отключения участника"""
        return self.create_event(
            EventType.LEAVE,
            {
                "user_id": str(self.current_user.id),
                "username": self.current_user.telegram_username,
                "role": self.role
            }
        )

    async def handle_start(self, data: dict) -> Event:
        """Обработка начала сессии"""
        self.stats.start_session()
        return self.create_event(EventType.START, data)

    async def handle_end(self, data: dict) -> list[Event]:
        """Обработка завершения сессии"""
        self.stats.end_session()
        
        # Создаем два события: завершение и итоговая статистика
        end_event = self.create_event(EventType.END, data)
        summary_event = self.create_event(
            EventType.RESULTS,
            self.stats.get_session_summary()
        )
        
        stats_manager.end_session(self.session_id)
        return [end_event, summary_event]

    async def handle_next(self, data: dict) -> list[Event]:
        """Обработка перехода к следующему вопросу"""
        self.stats.end_question()
        
        question_id = data.get("question_id")
        if question_id:
            self.stats.start_question(question_id)
            
        next_event = self.create_event(EventType.NEXT, data)
        stats_event = self.create_event(
            EventType.UPDATE,
            {
                "question_stats": self.stats.get_question_stats(question_id)
            } if question_id else {}
        )
        return [next_event, stats_event]

    async def handle_submit(self, data: dict) -> list[Event]:
        """Обработка ответа участника"""
        if "question_id" not in data or "selected_option" not in data:
            return []

        # Создаем и записываем статистику ответа
        answer = AnswerStats(
            question_id=data["question_id"],
            answer_time=data.get("answer_time", 0.0),
            is_correct=data.get("is_correct", False),
            selected_option=data["selected_option"]
        )
        self.stats.record_answer(str(self.current_user.id), answer)
        
        # Создаем события: ответ, обновление лидерборда и статистики вопроса
        submit_event = self.create_event(EventType.SUBMIT, data)
        leaderboard_event = self.create_event(
            EventType.UPDATE,
            {
                "leaderboard": self.stats.get_current_leaderboard(),
                "question_stats": self.stats.get_question_stats(data["question_id"])
            }
        )
        
        return [submit_event, leaderboard_event]

    async def handle_event(self, event: Event) -> list[Event]:
        """Основной метод обработки событий"""
        handlers = {
            EventType.START: self.handle_start,
            EventType.END: self.handle_end,
            EventType.NEXT: self.handle_next,
            EventType.ANSWER: self.handle_submit
        }
        
        handler = handlers.get(event.type)
        if not handler:
            return [event]
            
        result = await handler(event.data)
        return result if isinstance(result, list) else [result] 