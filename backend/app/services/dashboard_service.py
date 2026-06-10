"""Dashboard aggregation: KPIs, chart series and credit-card widgets.

Trends are computed by iterating month windows in Python (one bounded query
per metric per month) so the SQL stays portable across PostgreSQL and SQLite.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard
from app.models.expense import Expense
from app.models.income import Income
from app.models.investment import Investment
from app.services import networth_service
from app.services.cashback_engine import get_cashback_engine
from app.services.credit_card_service import available_credit, utilization_percent
from app.utils.dates import last_n_months, month_bounds
from app.utils.finance import money, percent


def _label(year: int, month: int) -> str:
    return f"{calendar.month_abbr[month]} {year}"


async def _sum(db: AsyncSession, column, *where) -> Decimal:
    return money(await db.scalar(select(func.coalesce(func.sum(column), 0)).where(*where)))


async def _income_between(db, uid, start, end) -> Decimal:
    return await _sum(db, Income.amount, Income.user_id == uid,
                      Income.received_date >= start, Income.received_date <= end)


async def _expense_between(db, uid, start, end) -> Decimal:
    return await _sum(db, Expense.amount, Expense.user_id == uid,
                      Expense.transaction_date >= start, Expense.transaction_date <= end)


async def _cashback_between(db, uid, start, end) -> Decimal:
    return await _sum(db, Expense.cashback_amount, Expense.user_id == uid,
                      Expense.transaction_date >= start, Expense.transaction_date <= end)


async def kpis(db: AsyncSession, user_id: int, *, reference: date) -> dict:
    start, end = month_bounds(reference)
    income = await _income_between(db, user_id, start, end)
    expenses = await _expense_between(db, user_id, start, end)
    cashback = await _cashback_between(db, user_id, start, end)
    cc_spend = await _sum(
        db, Expense.amount, Expense.user_id == user_id,
        Expense.credit_card_id.isnot(None),
        Expense.transaction_date >= start, Expense.transaction_date <= end,
    )
    # Cashback offsets spend: effective spend is net of it, and savings counts it.
    effective_expense = money(expenses - cashback)
    savings = money(income - effective_expense)
    investments = await _sum(db, Investment.current_value, Investment.user_id == user_id)
    nw = await networth_service.compute(db, user_id=user_id)

    return {
        "income": income,
        "expenses": expenses,
        "effective_expense": effective_expense,
        "cashback": cashback,
        "cc_spend": cc_spend,
        "savings": savings,
        "savings_rate": percent(savings, income),
        "investments": investments,
        "net_worth": nw.net_worth,
    }


async def expense_by_category(db, user_id, *, reference: date) -> list[dict]:
    start, end = month_bounds(reference)
    rows = (
        await db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == user_id,
                   Expense.transaction_date >= start,
                   Expense.transaction_date <= end)
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )
    ).all()
    return [{"category": cat.value, "amount": money(total)} for cat, total in rows]


async def fixed_vs_variable(db, user_id, *, reference: date) -> dict:
    start, end = month_bounds(reference)
    fixed = await _sum(db, Expense.amount, Expense.user_id == user_id,
                       Expense.transaction_date >= start, Expense.transaction_date <= end,
                       Expense.is_recurring.is_(True))
    variable = await _sum(db, Expense.amount, Expense.user_id == user_id,
                          Expense.transaction_date >= start, Expense.transaction_date <= end,
                          Expense.is_recurring.is_(False))
    return {"fixed": fixed, "variable": variable}


async def trends(db, user_id, *, reference: date, months: int) -> dict:
    monthly: list[dict] = []
    savings: list[dict] = []
    cashback: list[dict] = []
    investment: list[dict] = []

    for year, month, start, end in last_n_months(reference, months):
        label = _label(year, month)
        inc = await _income_between(db, user_id, start, end)
        exp = await _expense_between(db, user_id, start, end)
        cb = await _cashback_between(db, user_id, start, end)
        sav = money(inc - exp + cb)  # cashback counts toward savings
        # Cumulative capital deployed up to end-of-month.
        invested = await _sum(
            db, Investment.invested_amount,
            Investment.user_id == user_id,
            (Investment.purchase_date.is_(None)) | (Investment.purchase_date <= end),
        )
        monthly.append({"label": label, "income": inc, "expense": exp, "savings": sav})
        savings.append({"label": label, "savings": sav})
        cashback.append({"label": label, "cashback": cb})
        investment.append({"label": label, "invested": invested})

    return {
        "monthly_trend": monthly,
        "savings_trend": savings,
        "cashback_trend": cashback,
        "investment_trend": investment,
    }


async def credit_card_widgets(db, user_id, *, reference: date) -> list[dict]:
    start, end = month_bounds(reference)
    cards = (
        await db.execute(
            select(CreditCard).where(CreditCard.user_id == user_id).order_by(CreditCard.card_name)
        )
    ).scalars().all()

    engine = get_cashback_engine()
    out: list[dict] = []
    for card in cards:
        spend = await _sum(db, Expense.amount, Expense.user_id == user_id,
                           Expense.credit_card_id == card.id,
                           Expense.transaction_date >= start, Expense.transaction_date <= end)
        cb = await _sum(db, Expense.cashback_amount, Expense.user_id == user_id,
                        Expense.credit_card_id == card.id,
                        Expense.transaction_date >= start, Expense.transaction_date <= end)
        cap = await engine.cap_status(db, user_id=user_id, card=card, reference=reference)
        out.append({
            "card_id": card.id,
            "card_name": card.card_name,
            "issuer": card.issuer,
            "network": card.network.value,
            "last_four": card.last_four,
            "card_color": card.card_color,
            "credit_limit": money(card.credit_limit),
            "current_balance": money(card.current_balance),
            "available_credit": available_credit(card),
            "utilization_percent": utilization_percent(card),
            "spend_this_month": spend,
            "cashback_this_month": cb,
            "cashback_cap": money(cap[0]) if cap else None,
            "cashback_cap_used": money(cap[1]) if cap else None,
            "cashback_cap_remaining": money(cap[2]) if cap else None,
        })
    return out


async def build_dashboard(
    db: AsyncSession, user_id: int, *, reference: date | None = None, months: int = 6
) -> dict:
    reference = reference or date.today()
    data: dict = {
        "month": _label(reference.year, reference.month),
        "kpis": await kpis(db, user_id, reference=reference),
        "expense_by_category": await expense_by_category(db, user_id, reference=reference),
        "fixed_vs_variable": await fixed_vs_variable(db, user_id, reference=reference),
        "credit_cards": await credit_card_widgets(db, user_id, reference=reference),
    }
    data.update(await trends(db, user_id, reference=reference, months=months))
    return data
