"""Income CRUD. Mutations recompute the affected monthly summary."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.enums import IncomeCategory
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate
from app.services.summary_service import get_summary_service

router = APIRouter(prefix="/income", tags=["Income"])


async def _get_owned(db: SessionDep, user_id: int, income_id: int) -> Income:
    income = await db.get(Income, income_id)
    if income is None or income.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Income not found")
    return income


async def _recompute(db: SessionDep, user_id: int, *days: date) -> None:
    service = get_summary_service()
    seen: set[tuple[int, int]] = set()
    for d in days:
        if (d.year, d.month) in seen:
            continue
        seen.add((d.year, d.month))
        await service.recompute_month(db, user_id=user_id, year=d.year, month=d.month)


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
async def create_income(
    payload: IncomeCreate, current_user: CurrentUser, db: SessionDep
) -> IncomeRead:
    income = Income(user_id=current_user.id, **payload.model_dump())
    db.add(income)
    await db.flush()
    await _recompute(db, current_user.id, income.received_date)
    await db.refresh(income)
    return IncomeRead.model_validate(income)


@router.get("", response_model=list[IncomeRead])
async def list_income(
    current_user: CurrentUser,
    db: SessionDep,
    category: IncomeCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_recurring: bool | None = None,
) -> list[IncomeRead]:
    filters = [Income.user_id == current_user.id]
    if category is not None:
        filters.append(Income.category == category)
    if date_from is not None:
        filters.append(Income.received_date >= date_from)
    if date_to is not None:
        filters.append(Income.received_date <= date_to)
    if is_recurring is not None:
        filters.append(Income.is_recurring == is_recurring)
    rows = (
        await db.execute(
            select(Income).where(*filters).order_by(Income.received_date.desc())
        )
    ).scalars().all()
    return [IncomeRead.model_validate(r) for r in rows]


@router.get("/{income_id}", response_model=IncomeRead)
async def get_income(
    income_id: int, current_user: CurrentUser, db: SessionDep
) -> IncomeRead:
    return IncomeRead.model_validate(await _get_owned(db, current_user.id, income_id))


@router.put("/{income_id}", response_model=IncomeRead)
async def update_income(
    income_id: int, payload: IncomeUpdate, current_user: CurrentUser, db: SessionDep
) -> IncomeRead:
    income = await _get_owned(db, current_user.id, income_id)
    original = income.received_date
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(income, field, value)
    await db.flush()
    await _recompute(db, current_user.id, original, income.received_date)
    await db.refresh(income)
    return IncomeRead.model_validate(income)


@router.delete(
    "/{income_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_income(
    income_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    income = await _get_owned(db, current_user.id, income_id)
    day = income.received_date
    await db.delete(income)
    await db.flush()
    await _recompute(db, current_user.id, day)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
