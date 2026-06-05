"""Budget computation: period spend rollup and Green/Yellow/Red status."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.expense import Expense
from app.utils.dates import period_bounds
from app.utils.finance import money, percent


def status_for(percent_used: float) -> str:
    """Green < 75%, Yellow 75–99%, Red >= 100%."""
    if percent_used >= 100:
        return "red"
    if percent_used >= 75:
        return "yellow"
    return "green"


def current_window(budget: Budget, *, today: date | None = None) -> tuple[date, date]:
    """Active period window, clamped to the budget's start/end dates."""
    today = today or date.today()
    start, end = period_bounds(budget.period.value, today)
    if budget.start_date and budget.start_date > start:
        start = budget.start_date
    if budget.end_date and budget.end_date < end:
        end = budget.end_date
    return start, end


async def compute_spent(
    db: AsyncSession, budget: Budget, *, today: date | None = None
) -> Decimal:
    """Sum expenses for the budget's category within the active window."""
    start, end = current_window(budget, today=today)
    total = await db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == budget.user_id,
            Expense.category == budget.category,
            Expense.transaction_date >= start,
            Expense.transaction_date <= end,
        )
    )
    return money(total)


def metrics(amount: Decimal, spent: Decimal) -> tuple[Decimal, float, str]:
    """Return ``(remaining, percent_used, status)`` for an amount/spend pair."""
    pct = percent(Decimal(str(spent)), Decimal(str(amount)))
    remaining = money(Decimal(str(amount)) - Decimal(str(spent)))
    return remaining, pct, status_for(pct)
