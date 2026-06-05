"""Investment CRUD plus a portfolio summary."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.enums import InvestmentType
from app.models.investment import Investment
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentRead,
    InvestmentTypeBreakdown,
    InvestmentUpdate,
    PortfolioSummary,
)
from app.services import investment_service
from app.utils.finance import money, percent

router = APIRouter(prefix="/investments", tags=["Investments"])


def _to_read(inv: Investment) -> InvestmentRead:
    return InvestmentRead.model_validate(
        {
            **{c.name: getattr(inv, c.name) for c in inv.__table__.columns},
            "returns_value": investment_service.returns_value(inv),
            "returns_percent": investment_service.returns_percent(inv),
        }
    )


async def _get_owned(db: SessionDep, user_id: int, inv_id: int) -> Investment:
    inv = await db.get(Investment, inv_id)
    if inv is None or inv.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Investment not found")
    return inv


@router.post("", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
async def create_investment(
    payload: InvestmentCreate, current_user: CurrentUser, db: SessionDep
) -> InvestmentRead:
    inv = Investment(user_id=current_user.id, **payload.model_dump())
    db.add(inv)
    await db.flush()
    await db.refresh(inv)
    return _to_read(inv)


@router.get("", response_model=list[InvestmentRead])
async def list_investments(
    current_user: CurrentUser,
    db: SessionDep,
    investment_type: InvestmentType | None = None,
) -> list[InvestmentRead]:
    filters = [Investment.user_id == current_user.id]
    if investment_type is not None:
        filters.append(Investment.investment_type == investment_type)
    rows = (
        await db.execute(
            select(Investment).where(*filters).order_by(Investment.name)
        )
    ).scalars().all()
    return [_to_read(i) for i in rows]


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary(
    current_user: CurrentUser, db: SessionDep
) -> PortfolioSummary:
    rows = (
        await db.execute(
            select(Investment).where(Investment.user_id == current_user.id)
        )
    ).scalars().all()

    total_invested = Decimal("0")
    total_current = Decimal("0")
    grouped: dict[InvestmentType, list[Decimal]] = defaultdict(lambda: [Decimal("0"), Decimal("0")])
    for inv in rows:
        invested = Decimal(str(inv.invested_amount))
        current = Decimal(str(inv.current_value))
        total_invested += invested
        total_current += current
        grouped[inv.investment_type][0] += invested
        grouped[inv.investment_type][1] += current

    by_type = [
        InvestmentTypeBreakdown(
            investment_type=t,
            invested_amount=money(inv),
            current_value=money(cur),
            returns_value=money(cur - inv),
            returns_percent=percent(cur - inv, inv),
        )
        for t, (inv, cur) in sorted(grouped.items(), key=lambda kv: kv[0].value)
    ]

    return PortfolioSummary(
        total_invested=money(total_invested),
        total_current_value=money(total_current),
        total_returns=money(total_current - total_invested),
        total_returns_percent=percent(total_current - total_invested, total_invested),
        by_type=by_type,
    )


@router.get("/{inv_id}", response_model=InvestmentRead)
async def get_investment(
    inv_id: int, current_user: CurrentUser, db: SessionDep
) -> InvestmentRead:
    return _to_read(await _get_owned(db, current_user.id, inv_id))


@router.put("/{inv_id}", response_model=InvestmentRead)
async def update_investment(
    inv_id: int, payload: InvestmentUpdate, current_user: CurrentUser, db: SessionDep
) -> InvestmentRead:
    inv = await _get_owned(db, current_user.id, inv_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    await db.flush()
    await db.refresh(inv)
    return _to_read(inv)


@router.delete(
    "/{inv_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_investment(
    inv_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    inv = await _get_owned(db, current_user.id, inv_id)
    await db.delete(inv)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
