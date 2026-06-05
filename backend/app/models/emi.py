"""EMI / loan model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import LoanType

if TYPE_CHECKING:
    from app.models.user import User


class EMI(Base, TimestampMixin):
    __tablename__ = "emis"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    loan_name: Mapped[str] = mapped_column(String(120), nullable=False)
    loan_type: Mapped[LoanType] = mapped_column(
        SAEnum(LoanType, native_enum=False, length=20),
        default=LoanType.PERSONAL,
        nullable=False,
    )
    lender: Mapped[str | None] = mapped_column(String(80))

    principal_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)

    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    months_paid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    total_payable: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(16, 2), default=Decimal("0"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="emis")
