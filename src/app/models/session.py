import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import Participant, Quiz


class SessionStatus(enum.StrEnum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Session(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "sessions"
    repr_cols = ("id", "quiz_id", "join_code", "status")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)
    current_question_index: Mapped[int] = mapped_column(default=1)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    join_code: Mapped[str] = mapped_column(String(4))
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.WAITING)

    quiz: Mapped["Quiz"] = relationship(back_populates="sessions", lazy="selectin")
    participants: Mapped["Participant"] = relationship(back_populates="session", lazy="selectin")

    __table_args__ = (
        Index(
            "uq_waiting_session_join_code",
            join_code,
            unique=True,
            postgresql_where=(status == SessionStatus.WAITING.value.upper()),
        ),
    )
