"""Rewards engine.

Evaluates a card's configurable ``reward_rules`` (any reward type) against a
spend. Replaces the old code-based cashback registry; the four preset cards are
now seeded as ``reward_rules`` rows that produce identical numbers.

Reward maths
------------
* cashback        -> reward_rate is a percent; units are ₹  (units = amount * rate/100)
* reward_points   -> reward_rate is points-per-₹; units are points (units = amount * rate)
* air_miles       -> reward_rate is miles-per-₹;  units are miles  (units = amount * rate)
* ₹ equivalent    -> units * point_value  (point_value defaults to 1 for cashback)

Monthly caps for cashback are enforced **per card, per calendar month** by
summing cashback already booked on the card that month (matching the historical
behaviour exactly). The engine exposes a backward-compatible ``CashbackResult``
for the expense flow plus a richer per-rule ``RewardResult``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard
from app.models.enums import CardRewardType, PaymentMethod, RewardAppliesTo, RewardType
from app.models.expense import Expense
from app.models.reward_rule import RewardRule
from app.utils.dates import month_bounds

_TWO = Decimal("0.01")
_ZERO = Decimal("0")

# Reward types that are earned per transaction (vs cycle-level milestones etc.).
TRANSACTIONAL = (RewardType.CASHBACK, RewardType.REWARD_POINTS, RewardType.AIR_MILES)

# Map the granular RewardType onto the coarse CardRewardType stored on expenses.
_TO_CARD_REWARD: dict[RewardType, CardRewardType] = {
    RewardType.CASHBACK: CardRewardType.CASHBACK,
    RewardType.REWARD_POINTS: CardRewardType.POINTS,
    RewardType.AIR_MILES: CardRewardType.MILES,
}


def _round(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_TWO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class SpendContext:
    """Normalized view of an expense used by rule predicates."""

    amount: Decimal
    merchant: str
    description: str
    payment_method: PaymentMethod
    is_online: bool
    category: str = ""


@dataclass(frozen=True)
class RewardResult:
    """Unified per-rule reward outcome."""

    reward_type: RewardType
    reward_units: Decimal
    reward_value_inr: Decimal
    eligible: bool


@dataclass(frozen=True)
class CashbackResult:
    """Backward-compatible result consumed by the expense flow.

    ``amount`` is always the ₹ equivalent of the transactional reward(s).
    """

    eligible: bool
    amount: Decimal
    reward_type: CardRewardType | None
    rule_id: str | None

    @classmethod
    def none(cls) -> "CashbackResult":
        return cls(eligible=False, amount=_ZERO, reward_type=None, rule_id=None)


@dataclass(frozen=True)
class RewardRuleEval:
    """Immutable, DB-decoupled view of a ``RewardRule`` for evaluation."""

    id: int
    name: str
    reward_type: RewardType
    applies_to: RewardAppliesTo
    rate: Decimal
    point_value: Decimal | None
    merchant_match: str | None
    category_match: str | None
    min_txn_amount: Decimal | None
    monthly_cap: Decimal | None
    milestone_threshold: Decimal | None
    milestone_reward: Decimal | None

    @classmethod
    def from_orm(cls, r: RewardRule) -> "RewardRuleEval":
        return cls(
            id=r.id,
            name=r.rule_name,
            reward_type=r.reward_type,
            applies_to=r.applies_to,
            rate=Decimal(str(r.reward_rate or 0)),
            point_value=None if r.point_value is None else Decimal(str(r.point_value)),
            merchant_match=(r.merchant_match or None),
            category_match=(r.category_match or None),
            min_txn_amount=None if r.min_txn_amount is None else Decimal(str(r.min_txn_amount)),
            monthly_cap=None if r.monthly_cap is None else Decimal(str(r.monthly_cap)),
            milestone_threshold=(
                None if r.milestone_threshold is None else Decimal(str(r.milestone_threshold))
            ),
            milestone_reward=(
                None if r.milestone_reward is None else Decimal(str(r.milestone_reward))
            ),
        )

    @property
    def is_transactional(self) -> bool:
        return self.reward_type in TRANSACTIONAL

    def spend_qualifies(self, ctx: SpendContext) -> bool:
        if self.min_txn_amount is not None and ctx.amount < self.min_txn_amount:
            return False
        a = self.applies_to
        if a == RewardAppliesTo.ALL:
            return True
        if a == RewardAppliesTo.ONLINE:
            return ctx.is_online
        if a == RewardAppliesTo.OFFLINE:
            return not ctx.is_online
        if a == RewardAppliesTo.UPI:
            return ctx.payment_method == PaymentMethod.UPI
        if a == RewardAppliesTo.MERCHANT_SPECIFIC:
            return bool(self.merchant_match) and self.merchant_match.lower() in ctx.merchant
        if a == RewardAppliesTo.CATEGORY_SPECIFIC:
            return bool(self.category_match) and self.category_match.lower() == ctx.category.lower()
        return False

    def reward_units(self, amount: Decimal) -> Decimal:
        if self.reward_type == RewardType.CASHBACK:
            return _round(amount * self.rate / Decimal("100"))
        return _round(amount * self.rate)

    def reward_value_inr(self, amount: Decimal) -> Decimal:
        units = self.reward_units(amount)
        pv = Decimal("1") if self.reward_type == RewardType.CASHBACK else (self.point_value or _ZERO)
        return _round(units * pv)

    def evaluate_txn(self, ctx: SpendContext) -> RewardResult:
        if not self.is_transactional or not self.spend_qualifies(ctx):
            return RewardResult(self.reward_type, _ZERO, _ZERO, False)
        return RewardResult(
            reward_type=self.reward_type,
            reward_units=self.reward_units(ctx.amount),
            reward_value_inr=self.reward_value_inr(ctx.amount),
            eligible=True,
        )


class RewardsEngine:
    """Evaluates a card's reward rules from the database."""

    async def load_rules(self, db: AsyncSession, card_id: int) -> list[RewardRuleEval]:
        rows = (
            await db.execute(select(RewardRule).where(RewardRule.card_id == card_id))
        ).scalars().all()
        return [RewardRuleEval.from_orm(r) for r in rows]

    async def transaction_rules(
        self, db: AsyncSession, card_id: int
    ) -> list[RewardRuleEval]:
        return [r for r in await self.load_rules(db, card_id) if r.is_transactional]

    async def evaluate(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        card: CreditCard | None,
        context: SpendContext,
        transaction_date,
        exclude_expense_id: int | None = None,
    ) -> CashbackResult:
        """Per-transaction reward as a ₹ amount (used by the expense flow)."""
        if card is None:
            return CashbackResult.none()

        rules = await self.transaction_rules(db, card.id)
        qualifying = [r for r in rules if r.spend_qualifies(context)]
        if not qualifying:
            return CashbackResult.none()

        primary = qualifying[0]
        total = _ZERO
        for rule in qualifying:
            value = rule.reward_value_inr(context.amount)
            if rule.reward_type == RewardType.CASHBACK and rule.monthly_cap is not None:
                used = await self._cashback_used_this_month(
                    db,
                    user_id=user_id,
                    card_id=card.id,
                    reference=transaction_date,
                    exclude_expense_id=exclude_expense_id,
                )
                remaining = rule.monthly_cap - used
                value = _ZERO if remaining <= _ZERO else min(value, _round(remaining))
            total += value

        return CashbackResult(
            eligible=True,
            amount=_round(total),
            reward_type=_TO_CARD_REWARD.get(primary.reward_type, CardRewardType.NONE),
            rule_id=str(primary.id),
        )

    async def cap_status(
        self, db: AsyncSession, *, user_id: int, card: CreditCard, reference
    ) -> tuple[Decimal, Decimal, Decimal] | None:
        """``(cap, used, remaining)`` for the card's capped cashback rule, else None."""
        rules = await self.load_rules(db, card.id)
        capped = next(
            (
                r
                for r in rules
                if r.reward_type == RewardType.CASHBACK and r.monthly_cap is not None
            ),
            None,
        )
        if capped is None:
            return None
        used = await self._cashback_used_this_month(
            db, user_id=user_id, card_id=card.id, reference=reference, exclude_expense_id=None
        )
        remaining = max(capped.monthly_cap - used, _ZERO)
        return capped.monthly_cap, used, remaining

    async def _cashback_used_this_month(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        card_id: int,
        reference,
        exclude_expense_id: int | None,
    ) -> Decimal:
        start, end = month_bounds(reference)
        stmt = select(func.coalesce(func.sum(Expense.cashback_amount), 0)).where(
            Expense.user_id == user_id,
            Expense.credit_card_id == card_id,
            Expense.transaction_date >= start,
            Expense.transaction_date <= end,
        )
        if exclude_expense_id is not None:
            stmt = stmt.where(Expense.id != exclude_expense_id)
        total = await db.scalar(stmt)
        return Decimal(str(total or 0))


# Process-wide singleton.
_engine = RewardsEngine()


def get_rewards_engine() -> RewardsEngine:
    return _engine


# Backward-compatible alias (older imports use ``get_cashback_engine``).
def get_cashback_engine() -> RewardsEngine:
    return _engine
