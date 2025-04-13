from datetime import datetime

from sqlalchemy import String, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid_v7.base import uuid7

from src.core.models import Base


class Organization(Base):
    __tablename__ = "organizations"
    repr_cols = ("id", "name")

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
