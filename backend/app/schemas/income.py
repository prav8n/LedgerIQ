"""Pydantic v2 schemas for income."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Frequency, IncomeCategory


class IncomeCreate(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category: IncomeCategory = IncomeCategory.SALARY
    frequency: Frequency = Frequency.MONTHLY
    received_date: date
    is_recurring: bool = False
    is_taxable: bool = True
    notes: str | None = None


class IncomeUpdate(BaseModel):
    source: str | None = Field(default=None, min_length=1, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category: IncomeCategory | None = None
    frequency: Frequency | None = None
    received_date: date | None = None
    is_recurring: bool | None = None
    is_taxable: bool | None = None
    notes: str | None = None


class IncomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    amount: Decimal
    category: IncomeCategory
    frequency: Frequency
    received_date: date
    is_recurring: bool
    is_taxable: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
