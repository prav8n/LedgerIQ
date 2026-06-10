"""Credit card CRUD with derived metrics, nested reward rules and a reward summary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.credit_card import CreditCard
from app.models.reward_rule import RewardRule
from app.schemas.credit_card import (
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
)
from app.schemas.reward_rule import (
    RewardRuleCreate,
    RewardRuleRead,
    RewardRuleUpdate,
)
from app.services import rewards_service
from app.services.credit_card_service import (
    available_credit,
    next_day_of_month,
    utilization_percent,
)
from app.services.rewards_engine import RewardRuleEval

router = APIRouter(prefix="/credit-cards", tags=["Credit Cards"])


async def _load_rule_rows(db: SessionDep, card_id: int) -> list[RewardRule]:
    return (
        await db.execute(
            select(RewardRule).where(RewardRule.card_id == card_id).order_by(RewardRule.id)
        )
    ).scalars().all()


async def _to_read(db: SessionDep, user_id: int, card: CreditCard) -> CreditCardRead:
    rule_rows = await _load_rule_rows(db, card.id)
    evals = [RewardRuleEval.from_orm(r) for r in rule_rows]
    summary = await rewards_service.build_card_summary(
        db, user_id=user_id, card=card, rules=evals
    )
    return CreditCardRead.model_validate(
        {
            **{c.name: getattr(card, c.name) for c in card.__table__.columns},
            "reward_rules": [RewardRuleRead.model_validate(r) for r in rule_rows],
            "available_credit": available_credit(card),
            "utilization_percent": utilization_percent(card),
            "next_statement_date": next_day_of_month(card.statement_day),
            "next_due_date": next_day_of_month(card.due_day),
            "reward_summary": summary,
        }
    )


async def _get_owned(db: SessionDep, user_id: int, card_id: int) -> CreditCard:
    card = await db.get(CreditCard, card_id)
    if card is None or card.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit card not found")
    return card


async def _get_owned_rule(
    db: SessionDep, card_id: int, rule_id: int
) -> RewardRule:
    rule = await db.get(RewardRule, rule_id)
    if rule is None or rule.card_id != card_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reward rule not found")
    return rule


# ----------------------------------------------------------------- cards
@router.post("", response_model=CreditCardRead, status_code=status.HTTP_201_CREATED)
async def create_card(
    payload: CreditCardCreate, current_user: CurrentUser, db: SessionDep
) -> CreditCardRead:
    data = payload.model_dump()
    rules = data.pop("reward_rules", [])
    card = CreditCard(user_id=current_user.id, **data)
    db.add(card)
    await db.flush()
    for rule in rules:
        db.add(RewardRule(card_id=card.id, **rule))
    await db.flush()
    await db.refresh(card)
    return await _to_read(db, current_user.id, card)


@router.get("", response_model=list[CreditCardRead])
async def list_cards(
    current_user: CurrentUser, db: SessionDep, is_active: bool | None = None
) -> list[CreditCardRead]:
    filters = [CreditCard.user_id == current_user.id]
    if is_active is not None:
        filters.append(CreditCard.is_active == is_active)
    rows = (
        await db.execute(
            select(CreditCard).where(*filters).order_by(CreditCard.card_name)
        )
    ).scalars().all()
    return [await _to_read(db, current_user.id, c) for c in rows]


@router.get("/{card_id}", response_model=CreditCardRead)
async def get_card(
    card_id: int, current_user: CurrentUser, db: SessionDep
) -> CreditCardRead:
    return await _to_read(db, current_user.id, await _get_owned(db, current_user.id, card_id))


@router.put("/{card_id}", response_model=CreditCardRead)
async def update_card(
    card_id: int, payload: CreditCardUpdate, current_user: CurrentUser, db: SessionDep
) -> CreditCardRead:
    card = await _get_owned(db, current_user.id, card_id)
    data = payload.model_dump(exclude_unset=True)
    rules = data.pop("reward_rules", None)
    for field, value in data.items():
        setattr(card, field, value)
    if rules is not None:
        # Replace the entire reward-rule set.
        for existing in await _load_rule_rows(db, card.id):
            await db.delete(existing)
        await db.flush()
        for rule in rules:
            db.add(RewardRule(card_id=card.id, **rule))
        await db.flush()
        # Keep stored expense rewards consistent with the new rules.
        await rewards_service.recompute_card_expenses(
            db, user_id=current_user.id, card=card
        )
    await db.flush()
    await db.refresh(card)
    return await _to_read(db, current_user.id, card)


@router.delete(
    "/{card_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_card(
    card_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    card = await _get_owned(db, current_user.id, card_id)
    await db.delete(card)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------- nested reward rules
@router.post(
    "/{card_id}/rules",
    response_model=RewardRuleRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_rule(
    card_id: int,
    payload: RewardRuleCreate,
    current_user: CurrentUser,
    db: SessionDep,
) -> RewardRuleRead:
    card = await _get_owned(db, current_user.id, card_id)
    rule = RewardRule(card_id=card_id, **payload.model_dump())
    db.add(rule)
    await db.flush()
    await rewards_service.recompute_card_expenses(db, user_id=current_user.id, card=card)
    await db.refresh(rule)
    return RewardRuleRead.model_validate(rule)


@router.put("/{card_id}/rules/{rule_id}", response_model=RewardRuleRead)
async def update_rule(
    card_id: int,
    rule_id: int,
    payload: RewardRuleUpdate,
    current_user: CurrentUser,
    db: SessionDep,
) -> RewardRuleRead:
    card = await _get_owned(db, current_user.id, card_id)
    rule = await _get_owned_rule(db, card_id, rule_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.flush()
    await rewards_service.recompute_card_expenses(db, user_id=current_user.id, card=card)
    await db.refresh(rule)
    return RewardRuleRead.model_validate(rule)


@router.delete(
    "/{card_id}/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_rule(
    card_id: int,
    rule_id: int,
    current_user: CurrentUser,
    db: SessionDep,
) -> Response:
    card = await _get_owned(db, current_user.id, card_id)
    rule = await _get_owned_rule(db, card_id, rule_id)
    await db.delete(rule)
    await db.flush()
    await rewards_service.recompute_card_expenses(db, user_id=current_user.id, card=card)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
