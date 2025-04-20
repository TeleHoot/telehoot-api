from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src import core


class User(core.models.sqlalchemy.Base):
    __tablename__ = "users"
    repr_cols = ("id", "telegram_username")
    username: Mapped[str | None] = mapped_column(String(255))

    telegram_id: Mapped[int] = mapped_column(unique=True)
    telegram_username: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(255))
