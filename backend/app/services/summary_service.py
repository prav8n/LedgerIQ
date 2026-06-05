"""Monthly summary recomputation.

Recomputes (and upserts) the ``monthly_summary`` row for a given user/month by
aggregating income and expenses. Call ``recompute_month`` after any income or
expense mutation; on edits that move a transaction across months, recompute
both the old and the new month.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExpenseCategory
from app.models.expense import Expense
from app.models.income import Income
from app.models.monthly_summary import MonthlySummary
from app.utils.dates import month_bounds

_ZERO = Decimal("0")


def _d(value) -> Decimal:
    return Decimal(str(value or 0))


class SummaryService:
    async def recompute_month(
        self, db: AsyncSession, *, user_id: int, year: int, month: int
    ) -> MonthlySummary:
        start, end = month_bounds(date(year, month, 1))

        total_income = _d(
            await db.scalar(
                select(func.coalesce(func.sum(Income.amount), 0)).where(
                    Income.user_id == user_id,
                    Income.received_date >= start,
                    Income.received_date <= end,
                )
            )
        )

        total_expense = _d(
            await db.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0)).where(
                    Expense.user_id == user_id,
                    Expense.transaction_date >= start,
                    Expense.transaction_date <= end,
                )
            )
        )

        # Investments tracked as expense rows categorized as INVESTMENT — an
        # informational subset of total_expense.
        total_investment = _d(
            await db.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0)).where(
                    Expense.user_id == user_id,
                    Expense.category == ExpenseCategory.INVESTMENT,
                    Expense.transaction_date >= start,
                    Expense.transaction_date <= end,
                )
            )
        )

        # Top spending category by total amount in the month.
        top_category_row = (
            await db.execute(
                select(Expense.category, func.sum(Expense.amount).label("total"))
                .where(
                    Expense.user_id == user_id,
                    Expense.transaction_date >= start,
                    Expense.transaction_date <= end,
                )
                .group_by(Expense.category)
                .order_by(func.sum(Expense.amount).desc())
                .limit(1)
            )
        ).first()
        top_category = (
            top_category_row[0].value if top_category_row else None
        )

        net_cashflow = total_income - total_expense

        summary = (
            await db.execute(
                select(MonthlySummary).where(
                    MonthlySummary.user_id == user_id,
                    MonthlySummary.year == year,
                    MonthlySummary.month == month,
                )
            )
        ).scalar_one_or_none()

        if summary is None:
            summary = MonthlySummary(user_id=user_id, year=year, month=month)
            db.add(summary)

        summary.total_income = total_income
        summary.total_expense = total_expense
        summary.total_investment = total_investment
        # Cash left after spending; mirrors net cashflow with the current model.
        summary.total_savings = net_cashflow
        summary.net_cashflow = net_cashflow
        summary.top_category = top_category

        await db.flush()
        return summary


_service = SummaryService()


def get_summary_service() -> SummaryService:
    return _service
