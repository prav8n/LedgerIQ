"""Expense CRUD, search, filtering and pagination.

Every write path runs three services in order:
1. categorization  — assign a category when the user didn't provide one,
2. cashback engine — compute card-linked cashback for the spend,
3. summary service — recompute the affected monthly_summary row(s).
"""

from __future__ import annotations

import math
from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.credit_card import CreditCard
from app.models.enums import ExpenseCategory, PaymentMethod
from app.models.expense import Expense
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseRead,
    ExpenseUpdate,
    PaginatedExpenses,
)
from app.services.cashback_engine import (
    CashbackResult,
    SpendContext,
    get_cashback_engine,
)
from app.services.categorization_service import get_categorizer
from app.services.summary_service import get_summary_service

router = APIRouter(prefix="/expenses", tags=["Expenses"])

_PAGE_SIZE = 20


# --------------------------------------------------------------- helpers
async def _get_owned_expense(db: SessionDep, user_id: int, expense_id: int) -> Expense:
    expense = await db.get(Expense, expense_id)
    if expense is None or expense.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )
    return expense


async def _get_owned_card(
    db: SessionDep, user_id: int, card_id: int | None
) -> CreditCard | None:
    if card_id is None:
        return None
    card = await db.get(CreditCard, card_id)
    if card is None or card.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit card not found for this user",
        )
    return card


async def _adjust_card_balance(
    db: SessionDep, user_id: int, card_id: int | None, delta: Decimal
) -> None:
    """Apply a signed change to a card's outstanding balance (floored at 0).

    Adding a card-paid expense raises the outstanding (and utilization);
    deleting/editing reverses it.
    """
    if not card_id or delta == 0:
        return
    card = await db.get(CreditCard, card_id)
    if card is None or card.user_id != user_id:
        return
    new_balance = Decimal(str(card.current_balance)) + Decimal(str(delta))
    card.current_balance = new_balance if new_balance > 0 else Decimal("0")


def _spend_context(expense: Expense) -> SpendContext:
    return SpendContext(
        amount=Decimal(str(expense.amount)),
        merchant=(expense.merchant or "").lower(),
        description=(expense.description or "").lower(),
        payment_method=expense.payment_method,
        is_online=expense.is_online,
        category=getattr(expense.category, "value", "") or "",
    )


def _apply_cashback(expense: Expense, result: CashbackResult) -> None:
    expense.cashback_eligible = result.eligible
    expense.cashback_amount = result.amount
    expense.cashback_type = result.reward_type
    expense.cashback_rule = result.rule_id


async def _recompute_summaries(
    db: SessionDep, user_id: int, *months: date
) -> None:
    summary_service = get_summary_service()
    seen: set[tuple[int, int]] = set()
    for d in months:
        key = (d.year, d.month)
        if key in seen:
            continue
        seen.add(key)
        await summary_service.recompute_month(
            db, user_id=user_id, year=d.year, month=d.month
        )


# ----------------------------------------------------------------- create
@router.post(
    "",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an expense",
)
async def create_expense(
    payload: ExpenseCreate, current_user: CurrentUser, db: SessionDep
) -> ExpenseRead:
    card = await _get_owned_card(db, current_user.id, payload.credit_card_id)

    expense = Expense(
        user_id=current_user.id,
        amount=payload.amount,
        subcategory=payload.subcategory,
        merchant=payload.merchant,
        description=payload.description,
        payment_method=payload.payment_method,
        transaction_date=payload.transaction_date,
        credit_card_id=payload.credit_card_id,
        reward_rule_id=payload.reward_rule_id if payload.credit_card_id else None,
        is_online=payload.is_online,
        is_recurring=payload.is_recurring,
        notes=payload.notes,
    )

    # 1) Categorization (user override wins).
    if payload.category is not None:
        expense.category = payload.category
        expense.is_ai_categorized = False
    else:
        result = await get_categorizer().categorize(
            merchant=payload.merchant,
            description=payload.description,
            amount=float(payload.amount),
        )
        expense.category = result.category
        expense.is_ai_categorized = True

    # 2) Cashback (needs the expense fields populated).
    cashback = await get_cashback_engine().evaluate(
        db,
        user_id=current_user.id,
        card=card,
        context=_spend_context(expense),
        transaction_date=expense.transaction_date,
        chosen_rule_id=expense.reward_rule_id,
    )
    _apply_cashback(expense, cashback)

    db.add(expense)
    await db.flush()

    # Reflect the spend on the card's outstanding balance / utilization.
    await _adjust_card_balance(
        db, current_user.id, expense.credit_card_id, expense.amount
    )

    # 3) Summary.
    await _recompute_summaries(db, current_user.id, expense.transaction_date)
    await db.refresh(expense)
    return ExpenseRead.model_validate(expense)


# ------------------------------------------------------------------- list
@router.get("", response_model=PaginatedExpenses, summary="List / search expenses")
async def list_expenses(
    current_user: CurrentUser,
    db: SessionDep,
    page: int = Query(1, ge=1),
    size: int = Query(_PAGE_SIZE, ge=1, le=100),
    q: str | None = Query(None, description="Search merchant / description / notes"),
    category: ExpenseCategory | None = None,
    payment_method: PaymentMethod | None = None,
    credit_card_id: int | None = None,
    rule_id: int | None = Query(None, description="Filter by the reward rule that earned"),
    date_from: date | None = None,
    date_to: date | None = None,
    min_amount: Decimal | None = Query(None, ge=0),
    max_amount: Decimal | None = Query(None, ge=0),
    sort: Literal["date", "amount", "category", "merchant", "cashback"] = "date",
    order: Literal["asc", "desc"] = "desc",
) -> PaginatedExpenses:
    filters = [Expense.user_id == current_user.id]
    if category is not None:
        filters.append(Expense.category == category)
    if payment_method is not None:
        filters.append(Expense.payment_method == payment_method)
    if credit_card_id is not None:
        filters.append(Expense.credit_card_id == credit_card_id)
    if rule_id is not None:
        # cashback_rule stores the id of the rule that actually earned.
        filters.append(Expense.cashback_rule == str(rule_id))
    if date_from is not None:
        filters.append(Expense.transaction_date >= date_from)
    if date_to is not None:
        filters.append(Expense.transaction_date <= date_to)
    if min_amount is not None:
        filters.append(Expense.amount >= min_amount)
    if max_amount is not None:
        filters.append(Expense.amount <= max_amount)
    if q:
        like = f"%{q.strip()}%"
        filters.append(
            or_(
                Expense.merchant.ilike(like),
                Expense.description.ilike(like),
                Expense.notes.ilike(like),
            )
        )

    total = await db.scalar(
        select(func.count()).select_from(Expense).where(*filters)
    )
    total = int(total or 0)

    sort_columns = {
        "date": Expense.transaction_date,
        "amount": Expense.amount,
        "category": Expense.category,
        "merchant": Expense.merchant,
        "cashback": Expense.cashback_amount,
    }
    sort_col = sort_columns[sort]
    ordering = sort_col.asc() if order == "asc" else sort_col.desc()

    rows = (
        await db.execute(
            select(Expense)
            .where(*filters)
            .order_by(ordering, Expense.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()

    return PaginatedExpenses(
        items=[ExpenseRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


# -------------------------------------------------------------------- get
@router.get("/{expense_id}", response_model=ExpenseRead, summary="Get an expense")
async def get_expense(
    expense_id: int, current_user: CurrentUser, db: SessionDep
) -> ExpenseRead:
    expense = await _get_owned_expense(db, current_user.id, expense_id)
    return ExpenseRead.model_validate(expense)


# ----------------------------------------------------------------- update
@router.put("/{expense_id}", response_model=ExpenseRead, summary="Update an expense")
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user: CurrentUser,
    db: SessionDep,
) -> ExpenseRead:
    expense = await _get_owned_expense(db, current_user.id, expense_id)
    original_month = expense.transaction_date
    old_card_id = expense.credit_card_id
    old_amount = Decimal(str(expense.amount))

    data = payload.model_dump(exclude_unset=True)
    category_provided = data.get("category") is not None
    merchant_or_desc_changed = "merchant" in data or "description" in data

    if "credit_card_id" in data:
        await _get_owned_card(db, current_user.id, data["credit_card_id"])

    # Apply scalar fields (category handled separately below).
    for field, value in data.items():
        if field == "category":
            continue
        setattr(expense, field, value)

    # Keep card outstanding balances in sync with the (possibly moved) spend:
    # back out the old card/amount, then apply the new one.
    await _adjust_card_balance(db, current_user.id, old_card_id, -old_amount)
    await _adjust_card_balance(
        db, current_user.id, expense.credit_card_id, Decimal(str(expense.amount))
    )

    # 1) Categorization.
    if category_provided:
        expense.category = data["category"]
        expense.is_ai_categorized = False
    elif merchant_or_desc_changed:
        result = await get_categorizer().categorize(
            merchant=expense.merchant,
            description=expense.description,
            amount=float(expense.amount),
        )
        expense.category = result.category
        expense.is_ai_categorized = True

    # 2) Cashback (re-evaluate, excluding this expense from its own cap usage).
    # A reward-rule choice only makes sense while a card is attached.
    if expense.credit_card_id is None:
        expense.reward_rule_id = None
    card = await _get_owned_card(db, current_user.id, expense.credit_card_id)
    cashback = await get_cashback_engine().evaluate(
        db,
        user_id=current_user.id,
        card=card,
        context=_spend_context(expense),
        transaction_date=expense.transaction_date,
        exclude_expense_id=expense.id,
        chosen_rule_id=expense.reward_rule_id,
    )
    _apply_cashback(expense, cashback)

    await db.flush()

    # 3) Summary — recompute both months if the transaction moved.
    await _recompute_summaries(
        db, current_user.id, original_month, expense.transaction_date
    )
    await db.refresh(expense)
    return ExpenseRead.model_validate(expense)


# ----------------------------------------------------------------- delete
@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an expense",
)
async def delete_expense(
    expense_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    expense = await _get_owned_expense(db, current_user.id, expense_id)
    month = expense.transaction_date
    card_id = expense.credit_card_id
    amount = Decimal(str(expense.amount))
    await db.delete(expense)
    await db.flush()
    # Remove the spend from the card's outstanding balance.
    await _adjust_card_balance(db, current_user.id, card_id, -amount)
    await _recompute_summaries(db, current_user.id, month)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
