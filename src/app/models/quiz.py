from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import Organization, Session, User


class Quiz(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "quizzes"
    __soft_delete_cascades__ = ("sessions",)
    repr_cols = ("id", "name", "is_public")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(500))
    is_public: Mapped[bool] = mapped_column(default=False)

    organization: Mapped["Organization"] = relationship(back_populates="quizzes", lazy="selectin")
    author: Mapped["User"] = relationship(back_populates="quizzes", lazy="selectin")
    sessions: Mapped[list["Session"]] = relationship(back_populates="quiz", lazy="selectin")
