import enum
import secrets
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Index, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import Quiz


class SessionStatus(enum.StrEnum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Session(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "sessions"
    repr_cols = ("id", "quiz_id", "join_code", "status")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    join_code: Mapped[str] = mapped_column(
        String(4), default=lambda: str(secrets.SystemRandom().randrange(0, 9999)).zfill(4)
    )
    status: Mapped[SessionStatus] = mapped_column(
        SQLAlchemyEnum(SessionStatus), default=SessionStatus.WAITING
    )

    quiz: Mapped["Quiz"] = relationship(back_populates="sessions", lazy="selectin")

    __table_args__ = (
        Index(
            "uq_waiting_session_join_code",
            join_code,
            unique=True,
            postgresql_where=(status == SessionStatus.WAITING),
        ),
    )

    @validates("join_code")
    def validate_join_code(self, join_code):
        if self.status != SessionStatus.WAITING:
            return join_code

        max_attempts = 10
        attempts = 0
        new_code = join_code

        while attempts < max_attempts:
            existing = Session.query.filter(  # type: ignore[valid-type]
                Session.join_code == new_code,
                Session.status == SessionStatus.WAITING,
                Session.id != self.id if self.id else None,
            ).first()

            if not existing:
                return new_code

            new_code = str(secrets.SystemRandom().randrange(0, 9999)).zfill(4)
            attempts += 1

        raise ValueError("Failed to generate unique join code after multiple attempts")
