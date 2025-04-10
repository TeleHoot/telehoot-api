from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base


class User(Base):
    __tablename__ = "users"
    repr_cols = ("id", "name")

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
