"""Per-card reward summary: earnings this month, milestone and fee-waiver progress.

Transactional rewards (cashback / points / miles) are summed over the current
calendar month (matching the cap window). Fee-waiver progress is tracked over
the current financial year (Apr–Mar); milestone progress over the current month.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard
from app.models.enums import RewardType
from app.models.expense import Expense
from app.services.rewards_engine import RewardRuleEval, SpendContext, get_rewards_engine
from app.utils.dates import financial_year_bounds, month_bounds
from app.utils.finance import money, percent

_ZERO = Decimal("0")


def _ctx(exp: Expense) -> SpendContext:
    return SpendContext(
        amount=Decimal(str(exp.amount)),
        merchant=(exp.merchant or "").lower(),
        description=(exp.description or "").lower(),
        payment_method=exp.payment_method,
        is_online=exp.is_online,
        category=getattr(exp.category, "value", "") or "",
    )


async def _card_spend(db: AsyncSession, user_id: int, card_id: int, start, end) -> Decimal:
    total = await db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == user_id,
            Expense.credit_card_id == card_id,
            Expense.transaction_date >= start,
            Expense.transaction_date <= end,
        )
    )
    return money(total)


async def build_card_summary(
    db: AsyncSession,
    *,
    user_id: int,
    card: CreditCard,
    rules: list[RewardRuleEval],
    reference: date | None = None,
) -> dict:
    reference = reference or date.today()
    m_start, m_end = month_bounds(reference)
    month_label = f"{calendar.month_abbr[reference.month]} {reference.year}"

    month_spend = await _card_spend(db, user_id, card.id, m_start, m_end)

    # Load this month's expenses once for per-rule earnings.
    month_expenses = (
        await db.execute(
            select(Expense).where(
                Expense.user_id == user_id,
                Expense.credit_card_id == card.id,
                Expense.transaction_date >= m_start,
                Expense.transaction_date <= m_end,
            )
        )
    ).scalars().all()

    # Accumulate per-rule units the same way the engine books them: an expense
    # with a forced reward_rule_id uses only that rule; otherwise the single best
    # qualifying rule applies (no stacking across rules for one transaction).
    txn_rules = [r for r in rules if r.is_transactional]
    by_id = {r.id: r for r in txn_rules}
    units_by_rule: dict[int, Decimal] = {r.id: _ZERO for r in txn_rules}
    for exp in month_expenses:
        ctx = _ctx(exp)
        chosen = getattr(exp, "reward_rule_id", None)
        if chosen is not None and chosen in by_id:
            forced = by_id[chosen]
            meets_min = (
                forced.min_txn_amount is None or ctx.amount >= forced.min_txn_amount
            )
            applicable = [forced] if meets_min else []
        else:
            qualifying = [r for r in txn_rules if r.spend_qualifies(ctx)]
            best = (
                max(qualifying, key=lambda r: r.reward_value_inr(ctx.amount))
                if qualifying
                else None
            )
            applicable = [best] if best is not None else []
        for rule in applicable:
            units_by_rule[rule.id] += rule.reward_units(ctx.amount)

    earnings: list[dict] = []
    total_value = _ZERO
    for rule in txn_rules:
        units = units_by_rule[rule.id]
        if units <= _ZERO:
            continue  # only show rules that actually earned this month
        capped = rule.monthly_cap is not None and units > rule.monthly_cap
        if capped:
            units = rule.monthly_cap
        pv = Decimal("1") if rule.reward_type == RewardType.CASHBACK else (rule.point_value or _ZERO)
        value = money(units * pv)
        total_value += value
        earnings.append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "reward_type": rule.reward_type,
                "reward_units": money(units),
                "reward_value_inr": value,
                "monthly_cap": rule.monthly_cap,
                "capped": capped,
            }
        )

    # Milestone progress (cycle = current month spend vs threshold).
    milestones: list[dict] = []
    for rule in rules:
        if rule.reward_type != RewardType.MILESTONE_BONUS or rule.milestone_threshold is None:
            continue
        threshold = rule.milestone_threshold
        milestones.append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "threshold": threshold,
                "progress": month_spend,
                "reward": rule.milestone_reward,
                "met": month_spend >= threshold,
                "percent": percent(month_spend, threshold),
            }
        )

    # Fee-waiver progress (cumulative spend this financial year vs threshold).
    fee_waiver = None
    if card.fee_waiver_spend_threshold:
        fy_start, fy_end = financial_year_bounds(reference)
        spent_fy = await _card_spend(db, user_id, card.id, fy_start, fy_end)
        threshold = Decimal(str(card.fee_waiver_spend_threshold))
        fee_waiver = {
            "threshold": threshold,
            "spent": spent_fy,
            "met": spent_fy >= threshold,
            "percent": percent(spent_fy, threshold),
        }

    # Non-monetary benefits (lounge access, vouchers) shown informationally.
    benefits = [
        rule.name
        for rule in rules
        if rule.reward_type in (RewardType.LOUNGE_ACCESS, RewardType.VOUCHER)
    ]

    return {
        "month_label": month_label,
        "month_spend": month_spend,
        "total_reward_value_inr": money(total_value),
        "earnings": earnings,
        "milestones": milestones,
        "fee_waiver": fee_waiver,
        "benefits": benefits,
    }


async def recompute_card_expenses(
    db: AsyncSession, *, user_id: int, card: CreditCard
) -> int:
    """Re-evaluate cashback for every expense on a card after its rules change.

    Clears any forced reward-rule choice that no longer exists, then re-runs the
    engine in chronological order (so monthly caps consume correctly), keeping
    each expense's stored cashback consistent with the card's current rules.
    """
    engine = get_rewards_engine()
    valid_rule_ids = {r.id for r in await engine.load_rules(db, card.id)}

    expenses = (
        await db.execute(
            select(Expense)
            .where(Expense.user_id == user_id, Expense.credit_card_id == card.id)
            .order_by(Expense.transaction_date, Expense.id)
        )
    ).scalars().all()
    if not expenses:
        return 0

    # Zero first so each cap re-accumulates cleanly in date order.
    for exp in expenses:
        exp.cashback_amount = _ZERO
    await db.flush()

    for exp in expenses:
        if exp.reward_rule_id is not None and exp.reward_rule_id not in valid_rule_ids:
            exp.reward_rule_id = None
        result = await engine.evaluate(
            db,
            user_id=user_id,
            card=card,
            context=SpendContext(
                amount=Decimal(str(exp.amount)),
                merchant=(exp.merchant or "").lower(),
                description=(exp.description or "").lower(),
                payment_method=exp.payment_method,
                is_online=exp.is_online,
                category=getattr(exp.category, "value", "") or "",
            ),
            transaction_date=exp.transaction_date,
            exclude_expense_id=exp.id,
            chosen_rule_id=exp.reward_rule_id,
        )
        exp.cashback_eligible = result.eligible
        exp.cashback_amount = result.amount
        exp.cashback_type = result.reward_type
        exp.cashback_rule = result.rule_id
        await db.flush()

    return len(expenses)
