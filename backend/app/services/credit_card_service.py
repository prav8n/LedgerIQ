"""Derived credit-card metrics (available credit, utilization, next dates)."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from app.models.credit_card import CreditCard
from app.utils.finance import money, percent


def available_credit(card: CreditCard) -> Decimal:
    return money(Decimal(str(card.credit_limit)) - Decimal(str(card.current_balance)))


def utilization_percent(card: CreditCard) -> float:
    return percent(Decimal(str(card.current_balance)), Decimal(str(card.credit_limit)))


def next_day_of_month(day: int | None, *, today: date | None = None) -> date | None:
    """Next calendar date that falls on day-of-month ``day`` (today inclusive)."""
    if not day:
        return None
    today = today or date.today()
    day = min(day, calendar.monthrange(today.year, today.month)[1])
    candidate = today.replace(day=day)
    if candidate >= today:
        return candidate
    # Roll to next month.
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))
