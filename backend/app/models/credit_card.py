"""Credit card model (feeds the cashback / rewards engine in a later phase)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CardNetwork, CardRewardType

if TYPE_CHECKING:
    from app.models.expense import Expense
    from app.models.reward_rule import RewardRule
    from app.models.user import User


class CreditCard(Base, TimestampMixin):
    __tablename__ = "credit_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    card_name: Mapped[str] = mapped_column(String(120), nullable=False)
    issuer: Mapped[str] = mapped_column(String(80), nullable=False)
    network: Mapped[CardNetwork] = mapped_column(
        SAEnum(CardNetwork, native_enum=False, length=20),
        default=CardNetwork.VISA,
        nullable=False,
    )
    last_four: Mapped[str | None] = mapped_column(String(4))
    card_color: Mapped[str | None] = mapped_column(String(20))

    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )

    # Day-of-month markers for the billing lifecycle (1-31).
    statement_day: Mapped[int | None] = mapped_column(Integer)
    due_day: Mapped[int | None] = mapped_column(Integer)
    billing_cycle_day: Mapped[int | None] = mapped_column(Integer)

    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))  # annual %
    annual_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    # Annual spend needed to waive the fee (None => fee not waivable by spend).
    fee_waiver_spend_threshold: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    reward_type: Mapped[CardRewardType] = mapped_column(
        SAEnum(CardRewardType, native_enum=False, length=20),
        default=CardRewardType.CASHBACK,
        nullable=False,
    )
    reward_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )  # base % or points-per-100

    valid_thru: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="credit_cards")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="credit_card")
    reward_rules: Mapped[list["RewardRule"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
