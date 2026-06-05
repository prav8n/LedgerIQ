"""Goal CRUD plus a contribution endpoint."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.enums import GoalStatus
from app.models.goal import Goal
from app.schemas.goal import (
    GoalContribution,
    GoalCreate,
    GoalRead,
    GoalUpdate,
)
from app.services import goal_service

router = APIRouter(prefix="/goals", tags=["Goals"])


def _to_read(goal: Goal) -> GoalRead:
    return GoalRead.model_validate(
        {
            **{c.name: getattr(goal, c.name) for c in goal.__table__.columns},
            "remaining": goal_service.remaining(goal),
            "progress_percent": goal_service.progress_percent(goal),
            "required_monthly_contribution": goal_service.required_monthly_contribution(goal),
        }
    )


async def _get_owned(db: SessionDep, user_id: int, goal_id: int) -> Goal:
    goal = await db.get(Goal, goal_id)
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found")
    return goal


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate, current_user: CurrentUser, db: SessionDep
) -> GoalRead:
    goal = Goal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return _to_read(goal)


@router.get("", response_model=list[GoalRead])
async def list_goals(
    current_user: CurrentUser, db: SessionDep, status_filter: GoalStatus | None = None
) -> list[GoalRead]:
    filters = [Goal.user_id == current_user.id]
    if status_filter is not None:
        filters.append(Goal.status == status_filter)
    rows = (
        await db.execute(
            select(Goal).where(*filters).order_by(Goal.priority.desc(), Goal.id)
        )
    ).scalars().all()
    return [_to_read(g) for g in rows]


@router.get("/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: int, current_user: CurrentUser, db: SessionDep
) -> GoalRead:
    return _to_read(await _get_owned(db, current_user.id, goal_id))


@router.put("/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: int, payload: GoalUpdate, current_user: CurrentUser, db: SessionDep
) -> GoalRead:
    goal = await _get_owned(db, current_user.id, goal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    if goal_service.is_reached(goal) and goal.status == GoalStatus.ACTIVE:
        goal.status = GoalStatus.COMPLETED
    await db.flush()
    await db.refresh(goal)
    return _to_read(goal)


@router.post("/{goal_id}/contribute", response_model=GoalRead)
async def contribute(
    goal_id: int,
    payload: GoalContribution,
    current_user: CurrentUser,
    db: SessionDep,
) -> GoalRead:
    goal = await _get_owned(db, current_user.id, goal_id)
    goal.current_amount = Decimal(str(goal.current_amount)) + payload.amount
    if goal_service.is_reached(goal) and goal.status == GoalStatus.ACTIVE:
        goal.status = GoalStatus.COMPLETED
    await db.flush()
    await db.refresh(goal)
    return _to_read(goal)


@router.delete(
    "/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_goal(
    goal_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    goal = await _get_owned(db, current_user.id, goal_id)
    await db.delete(goal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
