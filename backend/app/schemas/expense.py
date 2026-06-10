"""Pydantic v2 schemas for expenses."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CardRewardType, ExpenseCategory, PaymentMethod


# ----------------------------------------------------------------- requests
class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    # Optional: when omitted, the categorization engine assigns it.
    category: ExpenseCategory | None = None
    subcategory: str | None = Field(default=None, max_length=60)
    merchant: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    payment_method: PaymentMethod = PaymentMethod.UPI
    transaction_date: date
    credit_card_id: int | None = None
    # Optional: force a specific card reward rule (null => auto-match).
    reward_rule_id: int | None = None
    is_online: bool = False
    is_recurring: bool = False
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    """Partial update — only provided fields are changed."""

    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category: ExpenseCategory | None = None
    subcategory: str | None = Field(default=None, max_length=60)
    merchant: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    payment_method: PaymentMethod | None = None
    transaction_date: date | None = None
    credit_card_id: int | None = None
    reward_rule_id: int | None = None
    is_online: bool | None = None
    is_recurring: bool | None = None
    notes: str | None = None


# ---------------------------------------------------------------- responses
class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: ExpenseCategory
    subcategory: str | None
    merchant: str | None
    description: str | None
    payment_method: PaymentMethod
    transaction_date: date
    credit_card_id: int | None
    reward_rule_id: int | None
    is_online: bool
    is_recurring: bool
    is_ai_categorized: bool
    cashback_eligible: bool
    cashback_amount: Decimal
    cashback_type: CardRewardType | None
    cashback_rule: str | None
    created_at: datetime
    updated_at: datetime


class PaginatedExpenses(BaseModel):
    items: list[ExpenseRead]
    total: int
    page: int
    size: int
    pages: int
