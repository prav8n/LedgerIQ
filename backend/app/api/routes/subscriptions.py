"""Subscription CRUD plus a cost summary."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionSummary,
    SubscriptionUpdate,
)
from app.services import subscription_service
from app.utils.finance import money

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def _to_read(sub: Subscription) -> SubscriptionRead:
    return SubscriptionRead.model_validate(
        {
            **{c.name: getattr(sub, c.name) for c in sub.__table__.columns},
            "monthly_cost": subscription_service.monthly_cost(sub),
            "yearly_cost": subscription_service.yearly_cost(sub),
        }
    )


async def _get_owned(db: SessionDep, user_id: int, sub_id: int) -> Subscription:
    sub = await db.get(Subscription, sub_id)
    if sub is None or sub.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
    return sub


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate, current_user: CurrentUser, db: SessionDep
) -> SubscriptionRead:
    sub = Subscription(user_id=current_user.id, **payload.model_dump())
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return _to_read(sub)


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    current_user: CurrentUser,
    db: SessionDep,
    is_active: bool | None = None,
    upcoming_before: date | None = None,
) -> list[SubscriptionRead]:
    filters = [Subscription.user_id == current_user.id]
    if is_active is not None:
        filters.append(Subscription.is_active == is_active)
    if upcoming_before is not None:
        filters.append(Subscription.next_billing_date <= upcoming_before)
    rows = (
        await db.execute(
            select(Subscription)
            .where(*filters)
            .order_by(Subscription.next_billing_date)
        )
    ).scalars().all()
    return [_to_read(s) for s in rows]


@router.get("/summary", response_model=SubscriptionSummary)
async def summary(current_user: CurrentUser, db: SessionDep) -> SubscriptionSummary:
    rows = (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == current_user.id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalars().all()
    total_monthly = sum(
        (subscription_service.monthly_cost(s) for s in rows), Decimal("0")
    )
    return SubscriptionSummary(
        active_count=len(rows),
        total_monthly_cost=money(total_monthly),
        total_yearly_cost=money(total_monthly * 12),
    )


@router.get("/{sub_id}", response_model=SubscriptionRead)
async def get_subscription(
    sub_id: int, current_user: CurrentUser, db: SessionDep
) -> SubscriptionRead:
    return _to_read(await _get_owned(db, current_user.id, sub_id))


@router.put("/{sub_id}", response_model=SubscriptionRead)
async def update_subscription(
    sub_id: int, payload: SubscriptionUpdate, current_user: CurrentUser, db: SessionDep
) -> SubscriptionRead:
    sub = await _get_owned(db, current_user.id, sub_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)
    await db.flush()
    await db.refresh(sub)
    return _to_read(sub)


@router.delete(
    "/{sub_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_subscription(
    sub_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    sub = await _get_owned(db, current_user.id, sub_id)
    await db.delete(sub)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
