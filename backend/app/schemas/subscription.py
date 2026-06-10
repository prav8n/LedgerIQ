"""Pydantic v2 schemas for subscriptions."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Frequency, PaymentMethod, SubscriptionCategory


class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: SubscriptionCategory = SubscriptionCategory.OTHER
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    billing_cycle: Frequency = Frequency.MONTHLY
    start_date: date
    next_billing_date: date
    payment_method: PaymentMethod = PaymentMethod.AUTO_DEBIT
    credit_card_id: int | None = None
    reward_rule_id: int | None = None
    reminder_days: int = Field(default=3, ge=0, le=60)
    auto_renew: bool = True
    is_active: bool = True


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: SubscriptionCategory | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    billing_cycle: Frequency | None = None
    start_date: date | None = None
    next_billing_date: date | None = None
    payment_method: PaymentMethod | None = None
    credit_card_id: int | None = None
    reward_rule_id: int | None = None
    reminder_days: int | None = Field(default=None, ge=0, le=60)
    auto_renew: bool | None = None
    is_active: bool | None = None


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: SubscriptionCategory
    amount: Decimal
    billing_cycle: Frequency
    start_date: date
    next_billing_date: date
    payment_method: PaymentMethod
    credit_card_id: int | None
    reward_rule_id: int | None
    reminder_days: int
    auto_renew: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Derived.
    monthly_cost: Decimal
    yearly_cost: Decimal


class SubscriptionSummary(BaseModel):
    active_count: int
    total_monthly_cost: Decimal
    total_yearly_cost: Decimal
