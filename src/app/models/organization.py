from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models import Base
from src.core.models.soft_delete import SoftDeleteMixin


class Organization(Base, SoftDeleteMixin):
    __tablename__ = "organizations"
    repr_cols = ("id", "name")

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
