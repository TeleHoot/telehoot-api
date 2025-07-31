import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, PrimaryKeyConstraint
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models import Organization, User


class UserRoles(enum.StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    PRESENTER = "presenter"


class Statuses(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class Membership(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "memberships"
    __table_args__ = (PrimaryKeyConstraint("organization_id", "user_id"),)

    repr_cols = ("organization_id", "user_id", "role")

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    role: Mapped[UserRoles] = mapped_column(
        SQLAlchemyEnum(
            UserRoles,
            name="userroles_enum",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    status: Mapped[Statuses] = mapped_column(
        SQLAlchemyEnum(
            Statuses,
            name="statuses_enum",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=Statuses.PENDING,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships", lazy="selectin"
    )
    user: Mapped["User"] = relationship(back_populates="memberships", lazy="selectin")
