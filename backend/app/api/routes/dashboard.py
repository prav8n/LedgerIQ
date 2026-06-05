"""Dashboard aggregation route."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse, summary="Dashboard overview")
async def get_dashboard(
    current_user: CurrentUser,
    db: SessionDep,
    months: int = Query(6, ge=1, le=24, description="Months of trend history"),
    year: int | None = Query(None, ge=2000, le=2100, description="Reference year"),
    month: int | None = Query(None, ge=1, le=12, description="Reference month (1-12)"),
) -> DashboardResponse:
    # When both year and month are given, anchor the dashboard on that month;
    # otherwise default to the current month.
    reference = date(year, month, 1) if year is not None and month is not None else None
    data = await dashboard_service.build_dashboard(
        db, current_user.id, reference=reference, months=months
    )
    return DashboardResponse.model_validate(data)
