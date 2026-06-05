"""Pydantic v2 schemas for goals."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GoalCategory, GoalStatus, Priority


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    category: GoalCategory = GoalCategory.OTHER
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    monthly_contribution: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    target_date: date | None = None
    priority: Priority = Priority.MEDIUM
    status: GoalStatus = GoalStatus.ACTIVE
    icon: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=9)


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    category: GoalCategory | None = None
    target_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    monthly_contribution: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    target_date: date | None = None
    priority: Priority | None = None
    status: GoalStatus | None = None
    icon: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=9)


class GoalContribution(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    category: GoalCategory
    target_amount: Decimal
    current_amount: Decimal
    monthly_contribution: Decimal
    target_date: date | None
    priority: Priority
    status: GoalStatus
    icon: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime

    # Derived.
    remaining: Decimal
    progress_percent: float
    required_monthly_contribution: Decimal
