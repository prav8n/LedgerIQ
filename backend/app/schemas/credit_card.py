"""Pydantic v2 schemas for credit cards."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CardNetwork, CardRewardType, RewardType
from app.schemas.reward_rule import RewardRuleCreate, RewardRuleRead


class CreditCardCreate(BaseModel):
    card_name: str = Field(min_length=1, max_length=120)
    issuer: str = Field(min_length=1, max_length=80)
    network: CardNetwork = CardNetwork.VISA
    last_four: str | None = Field(default=None, min_length=4, max_length=4)
    card_color: str | None = Field(default=None, max_length=20)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    current_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    statement_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    billing_cycle_day: int | None = Field(default=None, ge=1, le=31)
    interest_rate: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=3)
    annual_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    fee_waiver_spend_threshold: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    reward_type: CardRewardType = CardRewardType.CASHBACK
    reward_rate: Decimal = Field(default=Decimal("0"), ge=0, max_digits=5, decimal_places=2)
    valid_thru: date | None = None
    is_active: bool = True
    reward_rules: list[RewardRuleCreate] = Field(default_factory=list)


class CreditCardUpdate(BaseModel):
    card_name: str | None = Field(default=None, min_length=1, max_length=120)
    issuer: str | None = Field(default=None, min_length=1, max_length=80)
    network: CardNetwork | None = None
    last_four: str | None = Field(default=None, min_length=4, max_length=4)
    card_color: str | None = Field(default=None, max_length=20)
    credit_limit: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    current_balance: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    statement_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    billing_cycle_day: int | None = Field(default=None, ge=1, le=31)
    interest_rate: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=3)
    annual_fee: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    fee_waiver_spend_threshold: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    reward_type: CardRewardType | None = None
    reward_rate: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    valid_thru: date | None = None
    is_active: bool | None = None
    # When provided, replaces the card's entire reward-rule set.
    reward_rules: list[RewardRuleCreate] | None = None


# ----------------------------------------------------------- reward summary
class RuleEarning(BaseModel):
    rule_id: int
    rule_name: str
    reward_type: RewardType
    reward_units: Decimal
    reward_value_inr: Decimal
    monthly_cap: Decimal | None
    capped: bool


class MilestoneProgress(BaseModel):
    rule_id: int
    rule_name: str
    threshold: Decimal
    progress: Decimal
    reward: Decimal | None
    met: bool
    percent: float


class FeeWaiverProgress(BaseModel):
    threshold: Decimal
    spent: Decimal
    met: bool
    percent: float


class CardRewardSummary(BaseModel):
    month_label: str
    month_spend: Decimal
    total_reward_value_inr: Decimal
    earnings: list[RuleEarning]
    milestones: list[MilestoneProgress]
    fee_waiver: FeeWaiverProgress | None
    benefits: list[str]


class CreditCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_name: str
    issuer: str
    network: CardNetwork
    last_four: str | None
    card_color: str | None
    credit_limit: Decimal
    current_balance: Decimal
    statement_day: int | None
    due_day: int | None
    billing_cycle_day: int | None
    interest_rate: Decimal | None
    annual_fee: Decimal
    fee_waiver_spend_threshold: Decimal | None
    reward_type: CardRewardType
    reward_rate: Decimal
    valid_thru: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    reward_rules: list[RewardRuleRead]

    # Derived (computed by the service layer at read time).
    available_credit: Decimal
    utilization_percent: float
    next_statement_date: date | None
    next_due_date: date | None
    reward_summary: CardRewardSummary
