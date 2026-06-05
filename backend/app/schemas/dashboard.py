"""Pydantic v2 schemas for the dashboard aggregation response."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class DashboardKpis(BaseModel):
    income: Decimal
    expenses: Decimal
    cashback: Decimal
    savings: Decimal
    savings_rate: float
    investments: Decimal
    net_worth: Decimal


class CategoryAmount(BaseModel):
    category: str
    amount: Decimal


class FixedVariable(BaseModel):
    fixed: Decimal
    variable: Decimal


class MonthlyTrendPoint(BaseModel):
    label: str
    income: Decimal
    expense: Decimal
    savings: Decimal


class SavingsTrendPoint(BaseModel):
    label: str
    savings: Decimal


class CashbackTrendPoint(BaseModel):
    label: str
    cashback: Decimal


class InvestmentTrendPoint(BaseModel):
    label: str
    invested: Decimal


class CreditCardWidget(BaseModel):
    card_id: int
    card_name: str
    issuer: str
    network: str
    last_four: str | None
    credit_limit: Decimal
    current_balance: Decimal
    available_credit: Decimal
    utilization_percent: float
    spend_this_month: Decimal
    cashback_this_month: Decimal
    cashback_cap: Decimal | None
    cashback_cap_used: Decimal | None
    cashback_cap_remaining: Decimal | None


class DashboardResponse(BaseModel):
    month: str
    kpis: DashboardKpis
    expense_by_category: list[CategoryAmount]
    fixed_vs_variable: FixedVariable
    credit_cards: list[CreditCardWidget]
    monthly_trend: list[MonthlyTrendPoint]
    savings_trend: list[SavingsTrendPoint]
    cashback_trend: list[CashbackTrendPoint]
    investment_trend: list[InvestmentTrendPoint]
