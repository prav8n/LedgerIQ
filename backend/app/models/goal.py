"""Savings goal model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import GoalCategory, GoalStatus, Priority

if TYPE_CHECKING:
    from app.models.user import User


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[GoalCategory] = mapped_column(
        SAEnum(GoalCategory, native_enum=False, length=20),
        default=GoalCategory.OTHER,
        nullable=False,
    )

    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    # Planned monthly contribution set by the user (the required amount to hit
    # the target by ``target_date`` is computed on read).
    monthly_contribution: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )

    target_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, native_enum=False, length=10),
        default=Priority.MEDIUM,
        nullable=False,
    )
    status: Mapped[GoalStatus] = mapped_column(
        SAEnum(GoalStatus, native_enum=False, length=20),
        default=GoalStatus.ACTIVE,
        nullable=False,
    )

    # Presentational metadata for the UI (icon key + hex color).
    icon: Mapped[str | None] = mapped_column(String(40))
    color: Mapped[str | None] = mapped_column(String(9))

    user: Mapped["User"] = relationship(back_populates="goals")
