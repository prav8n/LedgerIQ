"""Pydantic v2 schemas for net worth."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class NetWorthManualInput(BaseModel):
    """User-supplied buckets; auto buckets are computed server-side."""

    cash: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    property_value: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    other_assets: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    other_liabilities: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class NetWorthSnapshotInput(NetWorthManualInput):
    # Defaults to today server-side when omitted.
    snapshot_date: date | None = None


class NetWorthRead(BaseModel):
    cash: Decimal
    investments_value: Decimal
    property_value: Decimal
    other_assets: Decimal
    credit_card_debt: Decimal
    loans_debt: Decimal
    other_liabilities: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


class NetWorthSnapshotRead(NetWorthRead):
    model_config = ConfigDict(from_attributes=True)

    id: int
    snapshot_date: date
    created_at: datetime
