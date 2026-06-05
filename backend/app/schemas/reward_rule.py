"""Pydantic v2 schemas for credit-card reward rules."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RewardAppliesTo, RewardType


class RewardRuleBase(BaseModel):
    rule_name: str = Field(min_length=1, max_length=120)
    reward_type: RewardType = RewardType.CASHBACK
    # % for cashback, points/miles per ₹ otherwise.
    reward_rate: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=4)
    point_value: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=4)
    applies_to: RewardAppliesTo = RewardAppliesTo.ALL
    merchant_match: str | None = Field(default=None, max_length=120)
    category_match: str | None = Field(default=None, max_length=60)
    min_txn_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    monthly_cap: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    milestone_threshold: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    milestone_reward: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validate(self) -> "RewardRuleBase":
        # Cashback rate is a percentage: must be within 0-100.
        if self.reward_type == RewardType.CASHBACK and self.reward_rate > Decimal("100"):
            raise ValueError("Cashback rate (percent) cannot exceed 100")
        return self


class RewardRuleCreate(RewardRuleBase):
    pass


class RewardRuleUpdate(BaseModel):
    rule_name: str | None = Field(default=None, min_length=1, max_length=120)
    reward_type: RewardType | None = None
    reward_rate: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=4)
    point_value: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=4)
    applies_to: RewardAppliesTo | None = None
    merchant_match: str | None = Field(default=None, max_length=120)
    category_match: str | None = Field(default=None, max_length=60)
    min_txn_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    monthly_cap: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    milestone_threshold: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    milestone_reward: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    notes: str | None = Field(default=None, max_length=500)


class RewardRuleRead(RewardRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    created_at: datetime
    updated_at: datetime
