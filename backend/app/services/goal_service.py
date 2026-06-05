"""Goal computations: progress, remaining, required monthly contribution."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.goal import Goal
from app.utils.dates import months_between
from app.utils.finance import money, percent


def remaining(goal: Goal) -> Decimal:
    return money(
        max(Decimal(str(goal.target_amount)) - Decimal(str(goal.current_amount)), Decimal("0"))
    )


def progress_percent(goal: Goal) -> float:
    return min(
        percent(Decimal(str(goal.current_amount)), Decimal(str(goal.target_amount))),
        100.0,
    )


def required_monthly_contribution(goal: Goal, *, today: date | None = None) -> Decimal:
    """Amount/month needed to reach the target by ``target_date``."""
    left = remaining(goal)
    if left <= 0 or goal.target_date is None:
        return Decimal("0.00")
    months = max(months_between(today or date.today(), goal.target_date), 1)
    return money(left / months)


def is_reached(goal: Goal) -> bool:
    return Decimal(str(goal.current_amount)) >= Decimal(str(goal.target_amount))
