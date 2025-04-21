from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models import OrganizationUser


class Organization(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "organizations"
    repr_cols = ("id", "name")

    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(default=False)
    image_path: Mapped[str | None] = mapped_column(String(255))

    organizations_users: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="organization", lazy="selectin"
    )
