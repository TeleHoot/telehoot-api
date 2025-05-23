import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import ParticipantAnswer, Session, User


class ParticipantRole(enum.StrEnum):
    HOST = "host"
    GUEST = "guest"


class Participant(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "participants"
    __soft_delete_cascades__ = ("answers",)
    repr_cols = ("id", "session_nickname", "role")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))

    session_nickname: Mapped[str] = mapped_column(String(64))
    role: Mapped[ParticipantRole] = mapped_column(
        SQLAlchemyEnum(
            ParticipantRole,
            name="participantrole_enum",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=ParticipantRole.GUEST,
    )

    user: Mapped["User"] = relationship(back_populates="participants", lazy="selectin")
    session: Mapped["Session"] = relationship(back_populates="participants")
    answers: Mapped["ParticipantAnswer"] = relationship(back_populates="participant")
