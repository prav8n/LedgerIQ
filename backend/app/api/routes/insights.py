"""AI insights route."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.insight import InsightsResponse
from app.services.insights_service import get_insight_generator

router = APIRouter(prefix="/insights", tags=["AI Insights"])


@router.get("", response_model=InsightsResponse, summary="Generate insights")
async def get_insights(
    current_user: CurrentUser,
    db: SessionDep,
    period: Literal["weekly", "monthly", "yearly"] = Query("monthly"),
) -> InsightsResponse:
    generator = get_insight_generator()
    insights = await generator.generate(
        db, current_user.id, period=period, reference=date.today()
    )
    return InsightsResponse.model_validate({"period": period, "insights": insights})
