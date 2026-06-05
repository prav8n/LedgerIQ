"""Date helpers."""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def month_bounds(reference: date) -> tuple[date, date]:
    """Return ``(first_day, last_day)`` of the calendar month of ``reference``.

    Both bounds are inclusive, which suits ``BETWEEN`` / ``>= , <=`` filters on
    a ``Date`` column.
    """
    first = reference.replace(day=1)
    last_day = calendar.monthrange(reference.year, reference.month)[1]
    last = reference.replace(day=last_day)
    return first, last


def week_bounds(reference: date) -> tuple[date, date]:
    """Inclusive Monday..Sunday bounds of the week of ``reference``."""
    start = reference - timedelta(days=reference.weekday())
    return start, start + timedelta(days=6)


def quarter_bounds(reference: date) -> tuple[date, date]:
    """Inclusive bounds of the calendar quarter of ``reference``."""
    q = (reference.month - 1) // 3
    start_month = q * 3 + 1
    start = date(reference.year, start_month, 1)
    end_month = start_month + 2
    last_day = calendar.monthrange(reference.year, end_month)[1]
    return start, date(reference.year, end_month, last_day)


def year_bounds(reference: date) -> tuple[date, date]:
    """Inclusive Jan 1..Dec 31 bounds of the year of ``reference``."""
    return date(reference.year, 1, 1), date(reference.year, 12, 31)


def financial_year_bounds(reference: date) -> tuple[date, date]:
    """Inclusive Indian financial-year bounds (1 Apr .. 31 Mar) of ``reference``.

    The FY containing e.g. 2026-05-10 runs 2026-04-01 .. 2027-03-31, while
    2026-02-10 belongs to the FY 2025-04-01 .. 2026-03-31.
    """
    start_year = reference.year if reference.month >= 4 else reference.year - 1
    return date(start_year, 4, 1), date(start_year + 1, 3, 31)


def period_bounds(period: str, reference: date) -> tuple[date, date]:
    """Resolve a ``BudgetPeriod``-style string to inclusive date bounds."""
    return {
        "weekly": week_bounds,
        "monthly": month_bounds,
        "quarterly": quarter_bounds,
        "yearly": year_bounds,
        "financial_year": financial_year_bounds,
    }.get(period, month_bounds)(reference)


def add_months(reference: date, months: int) -> date:
    """Return ``reference`` shifted by ``months`` (clamped to month length)."""
    total = reference.month - 1 + months
    year = reference.year + total // 12
    month = total % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(reference.day, last_day))


def months_between(start: date, end: date) -> int:
    """Whole months from ``start`` to ``end`` (>= 0)."""
    if end <= start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month)


def last_n_months(reference: date, n: int) -> list[tuple[int, int, date, date]]:
    """Oldest-first list of ``(year, month, first_day, last_day)`` ending at
    the month of ``reference`` (inclusive), spanning ``n`` months."""
    out: list[tuple[int, int, date, date]] = []
    for offset in range(n - 1, -1, -1):
        ref = add_months(reference.replace(day=1), -offset)
        start, end = month_bounds(ref)
        out.append((ref.year, ref.month, start, end))
    return out


def previous_period_ref(period: str, reference: date) -> date:
    """A date inside the period immediately preceding the one of ``reference``."""
    start, _ = period_bounds(period, reference)
    # One day before the current period's start lands in the previous period.
    return start - timedelta(days=1)
