"""Analytics aggregation: period KPIs, top categories, budget adherence,
cashback optimization and period-over-period growth."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.credit_card import CreditCard
from app.models.expense import Expense
from app.models.income import Income
from app.services import budget_service
from app.services.cashback_engine import get_cashback_engine
from app.utils.dates import period_bounds, previous_period_ref
from app.utils.finance import money, percent


async def _sum(db, column, *where) -> Decimal:
    return money(await db.scalar(select(func.coalesce(func.sum(column), 0)).where(*where)))


async def _window_aggregates(db, uid, start, end) -> dict:
    income = await _sum(db, Income.amount, Income.user_id == uid,
                        Income.received_date >= start, Income.received_date <= end)
    expense = await _sum(db, Expense.amount, Expense.user_id == uid,
                         Expense.transaction_date >= start, Expense.transaction_date <= end)
    cashback = await _sum(db, Expense.cashback_amount, Expense.user_id == uid,
                          Expense.transaction_date >= start, Expense.transaction_date <= end)
    savings = money(income - expense)
    return {
        "income": income,
        "expense": expense,
        "cashback": cashback,
        "savings": savings,
        "savings_rate": percent(savings, income),
    }


def _growth(current: Decimal, previous: Decimal) -> float:
    """Percent change from previous to current (0 when previous is 0)."""
    return percent(money(current - previous), previous)


async def _top_categories(db, uid, start, end, *, limit: int = 5) -> list[dict]:
    rows = (
        await db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == uid,
                   Expense.transaction_date >= start, Expense.transaction_date <= end)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
            .limit(limit)
        )
    ).all()
    total = money(sum((money(t) for _, t in rows), Decimal("0")))
    return [
        {"category": cat.value, "amount": money(t), "percent": percent(money(t), total)}
        for cat, t in rows
    ]


async def _budget_adherence(db, uid) -> list[dict]:
    budgets = (
        await db.execute(
            select(Budget).where(Budget.user_id == uid, Budget.is_active.is_(True))
            .order_by(Budget.category)
        )
    ).scalars().all()
    out: list[dict] = []
    for b in budgets:
        spent = await budget_service.compute_spent(db, b)
        remaining, pct, status = budget_service.metrics(b.amount, spent)
        out.append({
            "category": b.category.value,
            "amount": money(b.amount),
            "spent": spent,
            "remaining": remaining,
            "percent_used": pct,
            "status": status,
        })
    return out


async def _cashback_optimization(db, uid, start, end) -> dict:
    cards = (
        await db.execute(select(CreditCard).where(CreditCard.user_id == uid))
    ).scalars().all()
    engine = get_cashback_engine()
    total = Decimal("0")
    by_card: list[dict] = []
    for card in cards:
        spend = await _sum(db, Expense.amount, Expense.user_id == uid,
                           Expense.credit_card_id == card.id,
                           Expense.transaction_date >= start, Expense.transaction_date <= end)
        earned = await _sum(db, Expense.cashback_amount, Expense.user_id == uid,
                            Expense.credit_card_id == card.id,
                            Expense.transaction_date >= start, Expense.transaction_date <= end)
        total += earned
        cap = await engine.cap_status(db, user_id=uid, card=card, reference=end)
        by_card.append({
            "card_id": card.id,
            "card_name": card.card_name,
            "spend": spend,
            "cashback_earned": earned,
            "effective_rate": percent(earned, spend),
            "cap": money(cap[0]) if cap else None,
            "cap_used": money(cap[1]) if cap else None,
            "cap_remaining": money(cap[2]) if cap else None,
        })
    by_card.sort(key=lambda c: c["cashback_earned"], reverse=True)
    return {"total_cashback": money(total), "by_card": by_card}


async def build_analytics(
    db: AsyncSession, user_id: int, *, period: str = "monthly", reference: date | None = None
) -> dict:
    reference = reference or date.today()
    start, end = period_bounds(period, reference)
    prev_ref = previous_period_ref(period, reference)
    prev_start, prev_end = period_bounds(period, prev_ref)

    current = await _window_aggregates(db, user_id, start, end)
    previous = await _window_aggregates(db, user_id, prev_start, prev_end)

    growth = {
        "income": _growth(current["income"], previous["income"]),
        "expense": _growth(current["expense"], previous["expense"]),
        "savings": _growth(current["savings"], previous["savings"]),
        "cashback": _growth(current["cashback"], previous["cashback"]),
    }

    return {
        "period": period,
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "kpis": current,
        "previous": previous,
        "growth": growth,
        "top_categories": await _top_categories(db, user_id, start, end),
        "budget_adherence": await _budget_adherence(db, user_id),
        "cashback_optimization": await _cashback_optimization(db, user_id, start, end),
    }
