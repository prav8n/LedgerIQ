"""Financial math helpers (rounding, EMI amortization, percentages)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")


def money(value: Decimal | float | int | str | None) -> Decimal:
    """Coerce to a 2-decimal ``Decimal`` (₹ amounts)."""
    return Decimal(str(value or 0)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def percent(part: Decimal, whole: Decimal) -> float:
    """Return ``part/whole`` as a percentage (0.0 when whole is 0)."""
    if not whole:
        return 0.0
    return float((Decimal(str(part)) / Decimal(str(whole)) * 100).quantize(TWO_PLACES))


def emi_amount(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """Standard reducing-balance EMI.

    EMI = P * r * (1+r)^n / ((1+r)^n - 1), where r is the monthly rate.
    Falls back to a straight-line split when the rate is zero.
    """
    if tenure_months <= 0:
        return ZERO
    p = Decimal(str(principal))
    if annual_rate is None or Decimal(str(annual_rate)) == ZERO:
        return money(p / tenure_months)
    r = Decimal(str(annual_rate)) / Decimal("1200")  # monthly fractional rate
    factor = (Decimal("1") + r) ** tenure_months
    return money(p * r * factor / (factor - Decimal("1")))
