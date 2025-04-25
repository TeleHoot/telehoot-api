from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.core.stats.models import (
    AnswerStats,
    ParticipantStats,
    QuestionStats
)


class BaseStatsHandler:
    """Базовый класс для обработчиков статистики"""
    def __init__(self, session_id: str):
        self.session_id = session_id


class ParticipantStatsHandler(BaseStatsHandler):
    """Обработчик статистики участников"""
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.participants: Dict[str, ParticipantStats] = {}

    def add_participant(self, user_id: str, username: str) -> ParticipantStats:
        if user_id not in self.participants:
            self.participants[user_id] = ParticipantStats(
                user_id=user_id,
                username=username
            )
        return self.participants[user_id]

    def record_answer(self, user_id: str, answer: AnswerStats):
        if user_id in self.participants:
            self.participants[user_id].add_answer(answer)

    def get_participant(self, user_id: str) -> Optional[ParticipantStats]:
        return self.participants.get(user_id)

    def get_leaderboard(self) -> List[ParticipantStats]:
        return sorted(
            self.participants.values(),
            key=lambda p: p.score,
            reverse=True
        )

    def get_top_players(self, limit: int = 3) -> List[dict]:
        return [
            {
                "username": p.username,
                "score": p.score,
                "correct_answers": p.correct_answers,
                "accuracy": p.correct_answers / p.total_answers if p.total_answers > 0 else 0
            }
            for p in self.get_leaderboard()[:limit]
        ]


class QuestionStatsHandler(BaseStatsHandler):
    """Обработчик статистики вопросов"""
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.questions: Dict[str, QuestionStats] = {}
        self.current_question_id: Optional[str] = None

    def start_question(self, question_id: str):
        self.current_question_id = question_id
        self.questions[question_id] = QuestionStats(
            question_id=question_id,
            start_time=datetime.now()
        )

    def end_question(self):
        if self.current_question_id and self.current_question_id in self.questions:
            self.questions[self.current_question_id].end_time = datetime.now()

    def record_answer(self, answer: AnswerStats):
        if self.current_question_id in self.questions:
            self.questions[self.current_question_id].add_answer(answer)

    def get_question_stats(self, question_id: str) -> Optional[QuestionStats]:
        return self.questions.get(question_id)

    def get_questions_summary(self) -> List[dict]:
        return [
            {
                "question_id": q_id,
                "correct_ratio": stats.correct_answers / stats.total_answers if stats.total_answers > 0 else 0,
                "avg_answer_time": stats.avg_answer_time or 0,
                "answer_distribution": stats.answer_distribution
            }
            for q_id, stats in self.questions.items()
        ]


class SessionStatsHandler(BaseStatsHandler):
    """Основной обработчик статистики сессии"""
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.participant_handler = ParticipantStatsHandler(session_id)
        self.question_handler = QuestionStatsHandler(session_id)

    def start_session(self):
        self.start_time = datetime.now()

    def end_session(self):
        self.end_time = datetime.now()
        self.question_handler.end_question()

    def add_participant(self, user_id: str, username: str):
        return self.participant_handler.add_participant(user_id, username)

    def start_question(self, question_id: str):
        self.question_handler.start_question(question_id)

    def end_question(self):
        self.question_handler.end_question()

    def record_answer(self, user_id: str, answer: AnswerStats):
        if not self.question_handler.current_question_id:
            return

        self.participant_handler.record_answer(user_id, answer)
        self.question_handler.record_answer(answer)

    def get_current_leaderboard(self) -> List[dict]:
        return [
            {
                "username": p.username,
                "score": p.score,
                "correct_answers": p.correct_answers
            }
            for p in self.participant_handler.get_leaderboard()
        ]

    def get_session_summary(self) -> dict:
        if not self.start_time:
            return {}

        total_duration = (
            (self.end_time or datetime.now()) - self.start_time
        ).total_seconds()

        return {
            "total_participants": len(self.participant_handler.participants),
            "total_questions": len(self.question_handler.questions),
            "duration_seconds": total_duration,
            "top_players": self.participant_handler.get_top_players(),
            "questions_stats": self.question_handler.get_questions_summary()
        } 