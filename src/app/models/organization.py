from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base, mixins


class Organization(Base, mixins.SoftDelete):
    __tablename__ = "organizations"
    repr_cols = ("id", "name")

    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(default=False)
