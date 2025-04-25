from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class AnswerStats(BaseModel):
    question_id: str
    answer_time: float  # время ответа в секундах
    is_correct: bool
    selected_option: str


class ParticipantStats(BaseModel):
    user_id: str
    username: str
    score: int = 0
    correct_answers: int = 0
    total_answers: int = 0
    answers: List[AnswerStats] = []
    avg_answer_time: float = 0.0
    
    def add_answer(self, answer: AnswerStats):
        self.answers.append(answer)
        self.total_answers += 1
        if answer.is_correct:
            self.correct_answers += 1
            # Формула подсчета очков: быстрее отвечаешь - больше очков
            # Максимум 1000 очков за вопрос, минимум 100 при правильном ответе
            score_for_answer = max(100, int(1000 * (1 - min(answer.answer_time / 15.0, 0.9))))
            self.score += score_for_answer
        
        # Обновляем среднее время ответа
        total_time = sum(a.answer_time for a in self.answers)
        self.avg_answer_time = total_time / len(self.answers)


class QuestionStats(BaseModel):
    question_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_answers: int = 0
    correct_answers: int = 0
    answer_distribution: Dict[str, int] = {}  # option_id -> count
    fastest_answer: Optional[float] = None
    slowest_answer: Optional[float] = None
    avg_answer_time: Optional[float] = None

    def add_answer(self, answer: AnswerStats):
        self.total_answers += 1
        if answer.is_correct:
            self.correct_answers += 1
        
        # Обновляем распределение ответов
        self.answer_distribution[answer.selected_option] = (
            self.answer_distribution.get(answer.selected_option, 0) + 1
        )
        
        # Обновляем статистику времени
        if self.fastest_answer is None or answer.answer_time < self.fastest_answer:
            self.fastest_answer = answer.answer_time
        if self.slowest_answer is None or answer.answer_time > self.slowest_answer:
            self.slowest_answer = answer.answer_time
            
        # Обновляем среднее время
        if self.avg_answer_time is None:
            self.avg_answer_time = answer.answer_time
        else:
            self.avg_answer_time = (
                (self.avg_answer_time * (self.total_answers - 1) + answer.answer_time)
                / self.total_answers
            )


class SessionStats:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.participants: Dict[str, ParticipantStats] = {}
        self.questions: Dict[str, QuestionStats] = {}
        self.current_question_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start_session(self):
        self.start_time = datetime.now()

    def end_session(self):
        self.end_time = datetime.now()
        if self.current_question_id and self.current_question_id in self.questions:
            self.questions[self.current_question_id].end_time = self.end_time

    def start_question(self, question_id: str):
        self.current_question_id = question_id
        self.questions[question_id] = QuestionStats(
            question_id=question_id,
            start_time=datetime.now()
        )

    def end_question(self):
        if self.current_question_id and self.current_question_id in self.questions:
            self.questions[self.current_question_id].end_time = datetime.now()

    def add_participant(self, user_id: str, username: str):
        if user_id not in self.participants:
            self.participants[user_id] = ParticipantStats(
                user_id=user_id,
                username=username
            )

    def record_answer(self, user_id: str, answer: AnswerStats):
        if not self.current_question_id:
            return
            
        # Обновляем статистику участника
        if user_id in self.participants:
            self.participants[user_id].add_answer(answer)
            
        # Обновляем статистику вопроса
        if self.current_question_id in self.questions:
            self.questions[self.current_question_id].add_answer(answer)

    def get_current_leaderboard(self) -> List[ParticipantStats]:
        """Получить текущий список лидеров, отсортированный по очкам"""
        return sorted(
            self.participants.values(),
            key=lambda p: p.score,
            reverse=True
        )

    def get_question_stats(self, question_id: str) -> Optional[QuestionStats]:
        """Получить статистику по конкретному вопросу"""
        return self.questions.get(question_id)

    def get_session_summary(self) -> dict:
        """Получить общую статистику сессии"""
        if not self.start_time:
            return {}

        total_duration = (
            (self.end_time or datetime.now()) - self.start_time
        ).total_seconds()

        return {
            "total_participants": len(self.participants),
            "total_questions": len(self.questions),
            "duration_seconds": total_duration,
            "top_players": [
                {
                    "username": p.username,
                    "score": p.score,
                    "correct_answers": p.correct_answers,
                    "accuracy": p.correct_answers / p.total_answers if p.total_answers > 0 else 0
                }
                for p in self.get_current_leaderboard()[:3]
            ],
            "questions_stats": [
                {
                    "question_id": q_id,
                    "correct_ratio": stats.correct_answers / stats.total_answers if stats.total_answers > 0 else 0,
                    "avg_answer_time": stats.avg_answer_time or 0,
                    "answer_distribution": stats.answer_distribution
                }
                for q_id, stats in self.questions.items()
            ]
        }


class SessionStatsManager:
    def __init__(self):
        self.sessions: Dict[str, SessionStats] = {}

    def create_session(self, session_id: str) -> SessionStats:
        self.sessions[session_id] = SessionStats(session_id)
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[SessionStats]:
        return self.sessions.get(session_id)

    def end_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].end_session()
            # Можно добавить сохранение статистики в базу данных
            del self.sessions[session_id]


# Глобальный менеджер статистики
stats_manager = SessionStatsManager() 