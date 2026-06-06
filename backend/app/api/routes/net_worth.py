"""Net-worth: live computation, snapshots and history."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.net_worth import NetWorthSnapshot
from app.schemas.net_worth import (
    NetWorthRead,
    NetWorthSnapshotInput,
    NetWorthSnapshotRead,
)
from app.services import networth_service

router = APIRouter(prefix="/net-worth", tags=["Net Worth"])


@router.get("/current", response_model=NetWorthRead)
async def current_net_worth(
    current_user: CurrentUser, db: SessionDep
) -> NetWorthRead:
    # Cash is derived live from tracked income/expenses, so it is NOT carried
    # forward (the stored snapshot cash already includes that flow). Other manual
    # buckets (property, other assets/liabilities) are carried forward.
    latest = await networth_service.latest_snapshot(db, current_user.id)
    comp = await networth_service.compute(
        db,
        user_id=current_user.id,
        cash=0,
        property_value=latest.property_value if latest else 0,
        other_assets=latest.other_assets if latest else 0,
        other_liabilities=latest.other_liabilities if latest else 0,
    )
    return NetWorthRead(**asdict(comp))


@router.post(
    "/snapshot",
    response_model=NetWorthSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    payload: NetWorthSnapshotInput, current_user: CurrentUser, db: SessionDep
) -> NetWorthSnapshotRead:
    comp = await networth_service.compute(
        db,
        user_id=current_user.id,
        cash=payload.cash,
        property_value=payload.property_value,
        other_assets=payload.other_assets,
        other_liabilities=payload.other_liabilities,
    )
    snap = await networth_service.upsert_snapshot(
        db,
        user_id=current_user.id,
        snapshot_date=payload.snapshot_date or date.today(),
        comp=comp,
    )
    await db.refresh(snap)
    return NetWorthSnapshotRead.model_validate(snap)


@router.get("", response_model=list[NetWorthSnapshotRead])
async def list_snapshots(
    current_user: CurrentUser, db: SessionDep
) -> list[NetWorthSnapshotRead]:
    rows = (
        await db.execute(
            select(NetWorthSnapshot)
            .where(NetWorthSnapshot.user_id == current_user.id)
            .order_by(NetWorthSnapshot.snapshot_date.desc())
        )
    ).scalars().all()
    return [NetWorthSnapshotRead.model_validate(r) for r in rows]


@router.delete(
    "/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_snapshot(
    snapshot_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    snap = await db.get(NetWorthSnapshot, snapshot_id)
    if snap is None or snap.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snapshot not found")
    await db.delete(snap)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
