"""Income source / receipt model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Frequency, IncomeCategory

if TYPE_CHECKING:
    from app.models.user import User


class Income(Base, TimestampMixin):
    __tablename__ = "income"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    source: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[IncomeCategory] = mapped_column(
        SAEnum(IncomeCategory, native_enum=False, length=20),
        default=IncomeCategory.SALARY,
        nullable=False,
    )
    frequency: Mapped[Frequency] = mapped_column(
        SAEnum(Frequency, native_enum=False, length=20),
        default=Frequency.MONTHLY,
        nullable=False,
    )
    received_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="incomes")
