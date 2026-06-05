"""Pydantic v2 schemas for AI insights."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

InsightType = Literal["positive", "warning", "tip", "info"]


class Insight(BaseModel):
    id: str
    type: InsightType
    title: str
    description: str
    category: str
    # Optional headline metric (already formatted by the caller if numeric).
    metric: str | None = None


class InsightsResponse(BaseModel):
    period: str
    insights: list[Insight]
