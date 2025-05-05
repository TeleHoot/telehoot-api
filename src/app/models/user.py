from typing import TYPE_CHECKING

from sqlalchemy import UUID, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import Membership, Quiz


class User(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "users"
    repr_cols = ("id", "telegram_username")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)
    username: Mapped[str | None] = mapped_column(String(255))

    is_admin: Mapped[bool] = mapped_column(default=False)

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(255))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="author")
