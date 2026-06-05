"""Investment holding model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import InvestmentType

if TYPE_CHECKING:
    from app.models.user import User


class Investment(Base, TimestampMixin):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    investment_type: Mapped[InvestmentType] = mapped_column(
        SAEnum(InvestmentType, native_enum=False, length=20),
        default=InvestmentType.MUTUAL_FUNDS,
        nullable=False,
    )
    platform: Mapped[str | None] = mapped_column(String(80))  # broker / AMC / bank
    symbol: Mapped[str | None] = mapped_column(String(40))  # ticker / scheme code

    invested_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(
        Numeric(16, 2), default=Decimal("0"), nullable=False
    )
    units: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    avg_buy_price: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))

    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))  # for FD/RD
    purchase_date: Mapped[date | None] = mapped_column(Date)
    maturity_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="investments")
