"""Subscription cost normalization and renewal advancement."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models.enums import Frequency
from app.models.subscription import Subscription
from app.utils.dates import add_months
from app.utils.finance import money

# Multipliers converting one charge of a given cycle into a monthly-equivalent.
_TO_MONTHLY: dict[Frequency, Decimal] = {
    Frequency.DAILY: Decimal("30"),
    Frequency.WEEKLY: Decimal("52") / Decimal("12"),
    Frequency.MONTHLY: Decimal("1"),
    Frequency.QUARTERLY: Decimal("1") / Decimal("3"),
    Frequency.YEARLY: Decimal("1") / Decimal("12"),
    Frequency.ONE_TIME: Decimal("0"),
}

_CYCLE_MONTHS: dict[Frequency, int] = {
    Frequency.MONTHLY: 1,
    Frequency.QUARTERLY: 3,
    Frequency.YEARLY: 12,
}


def monthly_cost(sub: Subscription) -> Decimal:
    factor = _TO_MONTHLY.get(sub.billing_cycle, Decimal("1"))
    return money(Decimal(str(sub.amount)) * factor)


def yearly_cost(sub: Subscription) -> Decimal:
    return money(monthly_cost(sub) * 12)


def advance_renewal(sub: Subscription, *, today: date | None = None) -> date:
    """Compute the next billing date after the current one elapses."""
    months = _CYCLE_MONTHS.get(sub.billing_cycle, 1)
    return add_months(sub.next_billing_date, months)
