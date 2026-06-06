"""Net-worth computation.

Asset/liability totals are assembled from live domain data where possible:
- investments_value <- sum of investment current values
- credit_card_debt  <- sum of credit-card current balances
- loans_debt        <- sum of outstanding EMI balances

Cash, property and "other" buckets are user-supplied (carried forward from the
most recent snapshot when not provided).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard
from app.models.emi import EMI
from app.models.expense import Expense
from app.models.income import Income
from app.models.investment import Investment
from app.models.net_worth import NetWorthSnapshot
from app.services import emi_service
from app.utils.finance import money


@dataclass
class NetWorthComputation:
    cash: Decimal
    investments_value: Decimal
    property_value: Decimal
    other_assets: Decimal
    credit_card_debt: Decimal
    loans_debt: Decimal
    other_liabilities: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


async def _sum(db: AsyncSession, column, *where) -> Decimal:
    return money(await db.scalar(select(func.coalesce(func.sum(column), 0)).where(*where)))


async def compute(
    db: AsyncSession,
    *,
    user_id: int,
    cash: Decimal = Decimal("0"),
    property_value: Decimal = Decimal("0"),
    other_assets: Decimal = Decimal("0"),
    other_liabilities: Decimal = Decimal("0"),
) -> NetWorthComputation:
    investments_value = await _sum(
        db, Investment.current_value, Investment.user_id == user_id
    )
    credit_card_debt = await _sum(
        db, CreditCard.current_balance, CreditCard.user_id == user_id
    )

    # Liquid cash flow from tracked activity: all income received, minus expenses
    # paid from cash/bank (NOT credit-card spend — that lives in credit_card_debt,
    # so counting it here too would be double-counting). Added to any manual cash.
    income_total = await _sum(db, Income.amount, Income.user_id == user_id)
    non_cc_expense_total = await _sum(
        db,
        Expense.amount,
        Expense.user_id == user_id,
        Expense.credit_card_id.is_(None),
    )
    cash = money(Decimal(str(cash)) + income_total - non_cc_expense_total)

    # EMI outstanding is a derived value, so sum it in Python.
    emis = (
        await db.execute(select(EMI).where(EMI.user_id == user_id, EMI.is_active.is_(True)))
    ).scalars().all()
    loans_debt = money(sum((emi_service.outstanding(e) for e in emis), Decimal("0")))

    total_assets = money(cash + investments_value + property_value + other_assets)
    total_liabilities = money(credit_card_debt + loans_debt + other_liabilities)

    return NetWorthComputation(
        cash=money(cash),
        investments_value=investments_value,
        property_value=money(property_value),
        other_assets=money(other_assets),
        credit_card_debt=credit_card_debt,
        loans_debt=loans_debt,
        other_liabilities=money(other_liabilities),
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=money(total_assets - total_liabilities),
    )


async def latest_snapshot(
    db: AsyncSession, user_id: int
) -> NetWorthSnapshot | None:
    return (
        await db.execute(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == user_id)
            .order_by(NetWorthSnapshot.snapshot_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def upsert_snapshot(
    db: AsyncSession, *, user_id: int, snapshot_date: date, comp: NetWorthComputation
) -> NetWorthSnapshot:
    existing = (
        await db.execute(
            select(NetWorthSnapshot).where(
                NetWorthSnapshot.user_id == user_id,
                NetWorthSnapshot.snapshot_date == snapshot_date,
            )
        )
    ).scalar_one_or_none()

    snap = existing or NetWorthSnapshot(user_id=user_id, snapshot_date=snapshot_date)
    snap.cash = comp.cash
    snap.investments_value = comp.investments_value
    snap.property_value = comp.property_value
    snap.other_assets = comp.other_assets
    snap.credit_card_debt = comp.credit_card_debt
    snap.loans_debt = comp.loans_debt
    snap.other_liabilities = comp.other_liabilities
    snap.total_assets = comp.total_assets
    snap.total_liabilities = comp.total_liabilities
    snap.net_worth = comp.net_worth
    if existing is None:
        db.add(snap)
    await db.flush()
    return snap
