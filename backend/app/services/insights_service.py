"""AI insights generation.

Rule-based today, structured behind an ``InsightGenerator`` interface so an
LLM-backed generator can be swapped in later (the route and callers won't
change). Each rule is a small async method returning zero or more insights.

Insight ``type`` drives the UI accent: positive | warning | tip | info.
"""

from __future__ import annotations

import abc
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.credit_card import CreditCard
from app.models.enums import RewardAppliesTo
from app.models.expense import Expense
from app.models.income import Income
from app.models.subscription import Subscription
from app.services import budget_service, subscription_service
from app.services.rewards_engine import RewardRuleEval, SpendContext, get_rewards_engine
from app.utils.dates import period_bounds, previous_period_ref
from app.utils.finance import money, percent

_PERIOD_WORD = {"weekly": "week", "monthly": "month", "yearly": "year"}


def _rule_hint(rule: RewardRuleEval) -> str:
    """Human label for what spend to route to a card, for optimization tips."""
    if rule.merchant_match:
        return rule.merchant_match.title()
    if rule.category_match:
        return rule.category_match.title()
    return {
        RewardAppliesTo.ONLINE: "online",
        RewardAppliesTo.OFFLINE: "offline",
        RewardAppliesTo.UPI: "UPI",
    }.get(rule.applies_to, "those")


async def _sum(db, column, *where) -> Decimal:
    return money(await db.scalar(select(func.coalesce(func.sum(column), 0)).where(*where)))


async def _category_totals(db, uid, start, end) -> dict[str, Decimal]:
    rows = (
        await db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == uid,
                   Expense.transaction_date >= start, Expense.transaction_date <= end)
            .group_by(Expense.category)
        )
    ).all()
    return {cat.value: money(total) for cat, total in rows}


class InsightGenerator(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self, db: AsyncSession, user_id: int, *, period: str, reference: date
    ) -> list[dict]: ...


class RuleBasedInsightGenerator(InsightGenerator):
    async def generate(
        self, db: AsyncSession, user_id: int, *, period: str, reference: date
    ) -> list[dict]:
        word = _PERIOD_WORD.get(period, "month")
        start, end = period_bounds(period, reference)
        prev_ref = previous_period_ref(period, reference)
        prev_start, prev_end = period_bounds(period, prev_ref)

        insights: list[dict] = []
        insights += await self._category_changes(db, user_id, start, end, prev_start, prev_end, word)
        insights += await self._savings_rate(db, user_id, start, end, word)
        insights += await self._cashback_optimization(db, user_id, start, end, word)
        insights += await self._budget_alerts(db, user_id)
        insights += await self._subscriptions(db, user_id)
        return insights

    async def _category_changes(self, db, uid, start, end, p_start, p_end, word) -> list[dict]:
        current = await _category_totals(db, uid, start, end)
        previous = await _category_totals(db, uid, p_start, p_end)
        out: list[dict] = []
        # Focus on the largest current categories with a meaningful change.
        for cat, amount in sorted(current.items(), key=lambda kv: kv[1], reverse=True)[:5]:
            prev = previous.get(cat, Decimal("0"))
            if prev <= 0 or amount <= 0:
                continue
            change = percent(money(amount - prev), prev)
            if abs(change) < 10:
                continue
            label = cat.replace("_", " ").title()
            direction = "more" if change > 0 else "less"
            out.append({
                "id": f"cat_change_{cat}",
                "type": "warning" if change > 0 else "positive",
                "category": cat,
                "title": f"{label} spending {direction}",
                "description": f"You spent {abs(change):.0f}% {direction} on {label} "
                f"vs last {word} (₹{amount} vs ₹{prev}).",
                "metric": f"{'+' if change > 0 else ''}{change:.0f}%",
            })
        return out[:3]

    async def _savings_rate(self, db, uid, start, end, word) -> list[dict]:
        income = await _sum(db, Income.amount, Income.user_id == uid,
                            Income.received_date >= start, Income.received_date <= end)
        expense = await _sum(db, Expense.amount, Expense.user_id == uid,
                             Expense.transaction_date >= start, Expense.transaction_date <= end)
        if income <= 0:
            return []
        savings = money(income - expense)
        rate = percent(savings, income)
        if rate >= 20:
            return [{
                "id": "savings_rate",
                "type": "positive",
                "category": "savings",
                "title": "Strong savings rate",
                "description": f"You saved {rate:.0f}% of your income this {word} "
                f"(₹{savings}). Keep it up!",
                "metric": f"{rate:.0f}%",
            }]
        if rate < 0:
            return [{
                "id": "savings_rate",
                "type": "warning",
                "category": "savings",
                "title": "Spending exceeds income",
                "description": f"You spent more than you earned this {word} "
                f"(₹{money(expense - income)} over).",
                "metric": f"{rate:.0f}%",
            }]
        return [{
            "id": "savings_rate",
            "type": "tip",
            "category": "savings",
            "title": "Room to save more",
            "description": f"Your savings rate is {rate:.0f}% this {word}. Aim for 20%+ "
            f"by trimming your top discretionary categories.",
            "metric": f"{rate:.0f}%",
        }]

    async def _cashback_optimization(self, db, uid, start, end, word) -> list[dict]:
        cards = (
            await db.execute(select(CreditCard).where(CreditCard.user_id == uid))
        ).scalars().all()
        # Every transactional reward rule the user owns a card for.
        engine = get_rewards_engine()
        rule_cards: list[tuple[RewardRuleEval, CreditCard]] = []
        for card in cards:
            for rule in await engine.transaction_rules(db, card.id):
                rule_cards.append((rule, card))
        if not rule_cards:
            return []

        expenses = (
            await db.execute(
                select(Expense).where(
                    Expense.user_id == uid,
                    Expense.transaction_date >= start, Expense.transaction_date <= end,
                )
            )
        ).scalars().all()

        gains: dict[int, Decimal] = {}
        best_rule: dict[int, tuple[Decimal, RewardRuleEval]] = {}
        for exp in expenses:
            ctx = SpendContext(
                amount=Decimal(str(exp.amount)),
                merchant=(exp.merchant or "").lower(),
                description=(exp.description or "").lower(),
                payment_method=exp.payment_method,
                is_online=exp.is_online,
                category=getattr(exp.category, "value", "") or "",
            )
            for rule, card in rule_cards:
                if exp.credit_card_id == card.id:
                    continue
                if rule.spend_qualifies(ctx):
                    gain = rule.reward_value_inr(ctx.amount) - Decimal(str(exp.cashback_amount))
                    if gain > 0:
                        gains[card.id] = gains.get(card.id, Decimal("0")) + gain
                        if card.id not in best_rule or gain > best_rule[card.id][0]:
                            best_rule[card.id] = (gain, rule)

        out: list[dict] = []
        card_by_id = {c.id: c for c in cards}
        for card_id, gain in sorted(gains.items(), key=lambda kv: kv[1], reverse=True):
            if gain < 50:
                continue
            card = card_by_id[card_id]
            hint = _rule_hint(best_rule[card_id][1]) if card_id in best_rule else "those"
            out.append({
                "id": f"cashback_opt_{card_id}",
                "type": "tip",
                "category": "cashback",
                "title": "Earn more cashback",
                "description": f"Switching {hint} purchases to {card.card_name} could "
                f"increase cashback by ~₹{money(gain)} this {word}.",
                "metric": f"+₹{money(gain)}",
            })
        return out[:2]

    async def _budget_alerts(self, db, uid) -> list[dict]:
        budgets = (
            await db.execute(
                select(Budget).where(Budget.user_id == uid, Budget.is_active.is_(True))
            )
        ).scalars().all()
        out: list[dict] = []
        for b in budgets:
            spent = await budget_service.compute_spent(db, b)
            _, pct, status = budget_service.metrics(b.amount, spent)
            label = b.category.value.replace("_", " ").title()
            if status == "red":
                out.append({
                    "id": f"budget_{b.id}",
                    "type": "warning",
                    "category": "budget",
                    "title": f"{label} budget exceeded",
                    "description": f"You've used {pct:.0f}% of your ₹{b.amount} {label} "
                    f"budget (₹{spent} spent).",
                    "metric": f"{pct:.0f}%",
                })
            elif status == "yellow":
                out.append({
                    "id": f"budget_{b.id}",
                    "type": "tip",
                    "category": "budget",
                    "title": f"{label} budget running low",
                    "description": f"You're at {pct:.0f}% of your {label} budget. "
                    f"₹{money(b.amount - spent)} left.",
                    "metric": f"{pct:.0f}%",
                })
        return out[:3]

    async def _subscriptions(self, db, uid) -> list[dict]:
        subs = (
            await db.execute(
                select(Subscription).where(
                    Subscription.user_id == uid, Subscription.is_active.is_(True)
                )
            )
        ).scalars().all()
        if not subs:
            return []
        monthly = money(sum((subscription_service.monthly_cost(s) for s in subs), Decimal("0")))
        if monthly <= 0:
            return []
        return [{
            "id": "subscriptions_total",
            "type": "info",
            "category": "subscription",
            "title": "Recurring subscriptions",
            "description": f"You have {len(subs)} active subscriptions costing "
            f"₹{monthly}/month (₹{money(monthly * 12)}/year).",
            "metric": f"₹{monthly}/mo",
        }]


_generator: InsightGenerator = RuleBasedInsightGenerator()


def get_insight_generator() -> InsightGenerator:
    return _generator
