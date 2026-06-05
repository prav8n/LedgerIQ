"""Pydantic v2 schemas for investments."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InvestmentType


class InvestmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    investment_type: InvestmentType = InvestmentType.MUTUAL_FUNDS
    platform: str | None = Field(default=None, max_length=80)
    symbol: str | None = Field(default=None, max_length=40)
    invested_amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    current_value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=16, decimal_places=2)
    units: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=4)
    avg_buy_price: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=4)
    interest_rate: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=3)
    purchase_date: date | None = None
    maturity_date: date | None = None
    notes: str | None = None


class InvestmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    investment_type: InvestmentType | None = None
    platform: str | None = Field(default=None, max_length=80)
    symbol: str | None = Field(default=None, max_length=40)
    invested_amount: Decimal | None = Field(default=None, gt=0, max_digits=16, decimal_places=2)
    current_value: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=2)
    units: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=4)
    avg_buy_price: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=4)
    interest_rate: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=3)
    purchase_date: date | None = None
    maturity_date: date | None = None
    notes: str | None = None


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    investment_type: InvestmentType
    platform: str | None
    symbol: str | None
    invested_amount: Decimal
    current_value: Decimal
    units: Decimal | None
    avg_buy_price: Decimal | None
    interest_rate: Decimal | None
    purchase_date: date | None
    maturity_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Derived.
    returns_value: Decimal
    returns_percent: float


class InvestmentTypeBreakdown(BaseModel):
    investment_type: InvestmentType
    invested_amount: Decimal
    current_value: Decimal
    returns_value: Decimal
    returns_percent: float


class PortfolioSummary(BaseModel):
    total_invested: Decimal
    total_current_value: Decimal
    total_returns: Decimal
    total_returns_percent: float
    by_type: list[InvestmentTypeBreakdown]
