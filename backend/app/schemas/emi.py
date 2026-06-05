"""Pydantic v2 schemas for EMIs / loans."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LoanType


class EMICreate(BaseModel):
    loan_name: str = Field(min_length=1, max_length=120)
    loan_type: LoanType = LoanType.PERSONAL
    lender: str | None = Field(default=None, max_length=80)
    principal_amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    # Optional: derived from principal/rate/tenure when omitted or zero.
    emi_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    interest_rate: Decimal = Field(ge=0, max_digits=6, decimal_places=3)
    tenure_months: int = Field(gt=0)
    months_paid: int = Field(default=0, ge=0)
    start_date: date
    next_due_date: date
    amount_paid: Decimal = Field(default=Decimal("0"), ge=0, max_digits=16, decimal_places=2)
    is_active: bool = True


class EMIUpdate(BaseModel):
    loan_name: str | None = Field(default=None, min_length=1, max_length=120)
    loan_type: LoanType | None = None
    lender: str | None = Field(default=None, max_length=80)
    principal_amount: Decimal | None = Field(default=None, gt=0, max_digits=16, decimal_places=2)
    emi_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    interest_rate: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=3)
    tenure_months: int | None = Field(default=None, gt=0)
    months_paid: int | None = Field(default=None, ge=0)
    start_date: date | None = None
    next_due_date: date | None = None
    amount_paid: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=2)
    is_active: bool | None = None


class EMIRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    loan_name: str
    loan_type: LoanType
    lender: str | None
    principal_amount: Decimal
    emi_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    months_paid: int
    start_date: date
    next_due_date: date
    total_payable: Decimal | None
    amount_paid: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Derived.
    outstanding: Decimal
    remaining_months: int
    progress_percent: float
