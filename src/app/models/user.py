from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src import core


class User(core.models.sqlalchemy.Base):
    __tablename__ = "users"
    repr_cols = ("id", "name")

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    balance: Mapped[float] = mapped_column(default=0.0)
