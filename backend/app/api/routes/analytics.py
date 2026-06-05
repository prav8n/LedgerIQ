"""Analytics aggregation route."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.analytics import AnalyticsResponse
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse, summary="Analytics overview")
async def get_analytics(
    current_user: CurrentUser,
    db: SessionDep,
    period: Literal["monthly", "quarterly", "yearly", "financial_year"] = Query("monthly"),
    year: int | None = Query(None, ge=2000, le=2100, description="Anchor year"),
    month: int | None = Query(None, ge=1, le=12, description="Anchor month (1-12)"),
) -> AnalyticsResponse:
    # A date inside the desired period anchors both the current and the
    # period-over-period comparison; default to today when omitted.
    reference = date(year, month, 1) if year is not None and month is not None else None
    data = await analytics_service.build_analytics(
        db, current_user.id, period=period, reference=reference
    )
    return AnalyticsResponse.model_validate(data)
