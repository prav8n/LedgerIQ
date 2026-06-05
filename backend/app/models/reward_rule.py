"""Reward rule model — one credit card can have many reward rules.

Generalizes the old code-based cashback rules into a configurable, per-card
table supporting any reward type (cashback, points, miles, milestone bonuses,
fee waivers, lounge access, vouchers).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import RewardAppliesTo, RewardType

if TYPE_CHECKING:
    from app.models.credit_card import CreditCard


class RewardRule(Base, TimestampMixin):
    __tablename__ = "reward_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True, nullable=False
    )

    rule_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reward_type: Mapped[RewardType] = mapped_column(
        SAEnum(RewardType, native_enum=False, length=20),
        default=RewardType.CASHBACK,
        nullable=False,
    )
    # % for cashback, points-per-₹ for points, miles-per-₹ for miles.
    reward_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0"), nullable=False
    )
    # ₹ value of one point / mile, so every reward can show a ₹ equivalent.
    point_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    applies_to: Mapped[RewardAppliesTo] = mapped_column(
        SAEnum(RewardAppliesTo, native_enum=False, length=20),
        default=RewardAppliesTo.ALL,
        nullable=False,
    )
    merchant_match: Mapped[str | None] = mapped_column(String(120))
    category_match: Mapped[str | None] = mapped_column(String(60))

    min_txn_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    monthly_cap: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # Milestone bonus: spend `milestone_threshold` in a cycle -> earn `milestone_reward`.
    milestone_threshold: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    milestone_reward: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    notes: Mapped[str | None] = mapped_column(Text)

    card: Mapped["CreditCard"] = relationship(back_populates="reward_rules")
