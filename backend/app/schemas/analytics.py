"""Pydantic v2 schemas for the analytics aggregation response."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class PeriodKpis(BaseModel):
    income: Decimal
    expense: Decimal
    cashback: Decimal
    savings: Decimal
    savings_rate: float


class TopCategory(BaseModel):
    category: str
    amount: Decimal
    percent: float


class BudgetAdherence(BaseModel):
    category: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: float
    status: str


class CardCashback(BaseModel):
    card_id: int
    card_name: str
    spend: Decimal
    cashback_earned: Decimal
    effective_rate: float
    cap: Decimal | None
    cap_used: Decimal | None
    cap_remaining: Decimal | None


class CashbackOptimization(BaseModel):
    total_cashback: Decimal
    by_card: list[CardCashback]


class Growth(BaseModel):
    income: float
    expense: float
    savings: float
    cashback: float


class DateRange(BaseModel):
    start: str
    end: str


class AnalyticsResponse(BaseModel):
    period: str
    range: DateRange
    kpis: PeriodKpis
    previous: PeriodKpis
    growth: Growth
    top_categories: list[TopCategory]
    budget_adherence: list[BudgetAdherence]
    cashback_optimization: CashbackOptimization
