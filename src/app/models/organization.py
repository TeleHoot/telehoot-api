from typing import TYPE_CHECKING

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models import Membership


class Organization(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "organizations"
    repr_cols = ("id", "name", "is_verified")

    id: Mapped[UUID] = mapped_column(UUID(), primary_key=True, default=uuid7)

    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[str | None] = mapped_column(String(255))

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="organization", lazy="selectin"
    )
