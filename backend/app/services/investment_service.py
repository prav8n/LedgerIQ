"""Investment computations: absolute and percentage returns."""

from __future__ import annotations

from decimal import Decimal

from app.models.investment import Investment
from app.utils.finance import money, percent


def returns_value(inv: Investment) -> Decimal:
    return money(Decimal(str(inv.current_value)) - Decimal(str(inv.invested_amount)))


def returns_percent(inv: Investment) -> float:
    return percent(returns_value(inv), Decimal(str(inv.invested_amount)))
