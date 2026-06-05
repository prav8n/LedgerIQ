"""Pydantic v2 schemas for budgets."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BudgetPeriod, ExpenseCategory


class BudgetCreate(BaseModel):
    category: ExpenseCategory
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    start_date: date
    end_date: date | None = None
    rollover: bool = False
    is_active: bool = True


class BudgetUpdate(BaseModel):
    category: ExpenseCategory | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    period: BudgetPeriod | None = None
    start_date: date | None = None
    end_date: date | None = None
    rollover: bool | None = None
    is_active: bool | None = None


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ExpenseCategory
    amount: Decimal
    period: BudgetPeriod
    spent: Decimal
    start_date: date
    end_date: date | None
    rollover: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Derived.
    remaining: Decimal
    percent_used: float
    status: str  # "green" | "yellow" | "red"
