"""Expense / transaction model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CardRewardType, ExpenseCategory, PaymentMethod

if TYPE_CHECKING:
    from app.models.credit_card import CreditCard
    from app.models.user import User


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Set when the expense was paid with a tracked credit card.
    credit_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="SET NULL"), index=True
    )
    # User's explicit reward-rule choice for this spend (null => auto-match).
    reward_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("reward_rules.id", ondelete="SET NULL"), index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(
        SAEnum(ExpenseCategory, native_enum=False, length=20),
        default=ExpenseCategory.OTHER,
        nullable=False,
        index=True,
    )
    subcategory: Mapped[str | None] = mapped_column(String(60))
    merchant: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(255))
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, native_enum=False, length=20),
        default=PaymentMethod.UPI,
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    # Whether the spend happened on an online channel (drives some card rules).
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True once the categorization engine (rule-based now, LLM later) assigns
    # the category, rather than the user choosing it explicitly.
    is_ai_categorized: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # ---- Cashback engine output (populated on create / edit) ----
    cashback_eligible: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    cashback_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    cashback_type: Mapped[CardRewardType | None] = mapped_column(
        SAEnum(CardRewardType, native_enum=False, length=20)
    )
    # Identifier of the cashback rule that matched, for transparency / audit.
    cashback_rule: Mapped[str | None] = mapped_column(String(60))

    user: Mapped["User"] = relationship(back_populates="expenses")
    credit_card: Mapped["CreditCard | None"] = relationship(
        back_populates="expenses"
    )
