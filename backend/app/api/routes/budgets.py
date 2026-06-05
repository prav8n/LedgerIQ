"""Budget CRUD. Spend is computed live (read-only) so status is always current."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.services import budget_service

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _to_read(budget: Budget, spent: Decimal) -> BudgetRead:
    remaining, pct, st = budget_service.metrics(budget.amount, spent)
    return BudgetRead.model_validate(
        {
            **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
            "spent": spent,
            "remaining": remaining,
            "percent_used": pct,
            "status": st,
        }
    )


async def _get_owned(db: SessionDep, user_id: int, budget_id: int) -> Budget:
    budget = await db.get(Budget, budget_id)
    if budget is None or budget.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget not found")
    return budget


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreate, current_user: CurrentUser, db: SessionDep
) -> BudgetRead:
    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    await db.flush()
    spent = await budget_service.compute_spent(db, budget)
    budget.spent = spent  # keep the cached value fresh on writes
    await db.flush()
    await db.refresh(budget)
    return _to_read(budget, spent)


@router.get("", response_model=list[BudgetRead])
async def list_budgets(
    current_user: CurrentUser, db: SessionDep, is_active: bool | None = None
) -> list[BudgetRead]:
    filters = [Budget.user_id == current_user.id]
    if is_active is not None:
        filters.append(Budget.is_active == is_active)
    rows = (
        await db.execute(select(Budget).where(*filters).order_by(Budget.category))
    ).scalars().all()
    out = []
    for b in rows:
        spent = await budget_service.compute_spent(db, b)
        out.append(_to_read(b, spent))
    return out


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: int, current_user: CurrentUser, db: SessionDep
) -> BudgetRead:
    budget = await _get_owned(db, current_user.id, budget_id)
    spent = await budget_service.compute_spent(db, budget)
    return _to_read(budget, spent)


@router.put("/{budget_id}", response_model=BudgetRead)
async def update_budget(
    budget_id: int, payload: BudgetUpdate, current_user: CurrentUser, db: SessionDep
) -> BudgetRead:
    budget = await _get_owned(db, current_user.id, budget_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    await db.flush()
    spent = await budget_service.compute_spent(db, budget)
    budget.spent = spent
    await db.flush()
    await db.refresh(budget)
    return _to_read(budget, spent)


@router.delete(
    "/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_budget(
    budget_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    budget = await _get_owned(db, current_user.id, budget_id)
    await db.delete(budget)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
