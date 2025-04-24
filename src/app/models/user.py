from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models import Membership


class User(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "users"
    repr_cols = ("id", "telegram_username")
    username: Mapped[str | None] = mapped_column(String(255))

    is_admin: Mapped[bool] = mapped_column(default=False)

    telegram_id: Mapped[int] = mapped_column(unique=True)
    telegram_username: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(255))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user", lazy="selectin")
