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