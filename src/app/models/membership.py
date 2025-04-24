import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models import Organization, User


class UserRoles(enum.StrEnum):
    CREATOR = "creator"
    EDITOR = "editor"
    PRESENTER = "presenter"


class Statuses(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class Membership(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "memberships"
    repr_cols = ("id", "organization_id", "user_id", "role")

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    role: Mapped[UserRoles] = mapped_column()
    status: Mapped[Statuses] = mapped_column(default=Statuses.PENDING)

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships", lazy="selectin"
    )
    user: Mapped["User"] = relationship(back_populates="memberships", lazy="selectin")
