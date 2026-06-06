"""Rewards engine tests: reward rules per card, qualification, caps, reward types.

Verifies the preset cashback numbers are unchanged after generalizing the engine
to DB-backed ``reward_rules``, and exercises points/miles (₹-equivalent) rewards.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.security import hash_password
from app.models.credit_card import CreditCard
from app.models.enums import (
    ExpenseCategory,
    PaymentMethod,
    RewardAppliesTo,
    RewardType,
)
from app.models.expense import Expense
from app.models.reward_rule import RewardRule
from app.models.user import User
from app.services.rewards_engine import SpendContext, get_rewards_engine

TXN = date(2026, 6, 10)


async def _make_user(db) -> User:
    user = User(email="cb@example.com", hashed_password=hash_password("x"))
    db.add(user)
    await db.flush()
    return user


async def _make_card(db, user, **kw) -> CreditCard:
    card = CreditCard(user_id=user.id, **kw)
    db.add(card)
    await db.flush()
    return card


async def _add_rule(db, card, **kw) -> RewardRule:
    rule = RewardRule(card_id=card.id, **kw)
    db.add(rule)
    await db.flush()
    return rule


async def test_swiggy_threshold(db):
    """Swiggy HDFC earns 10% only on orders >= ₹249 (identical to old engine)."""
    user = await _make_user(db)
    card = await _make_card(db, user, card_name="Swiggy HDFC", issuer="HDFC")
    await _add_rule(
        db, card,
        rule_name="10% on Swiggy", reward_type=RewardType.CASHBACK,
        reward_rate=Decimal("10"), point_value=Decimal("1"),
        applies_to=RewardAppliesTo.MERCHANT_SPECIFIC, merchant_match="swiggy",
        min_txn_amount=Decimal("249"),
    )
    engine = get_rewards_engine()

    ok = SpendContext(Decimal("300"), "swiggy", "", PaymentMethod.CREDIT_CARD, False)
    res = await engine.evaluate(db, user_id=user.id, card=card, context=ok, transaction_date=TXN)
    assert res.eligible is True
    assert res.amount == Decimal("30.00")  # 10% of 300

    small = SpendContext(Decimal("200"), "swiggy", "", PaymentMethod.CREDIT_CARD, False)
    res2 = await engine.evaluate(db, user_id=user.id, card=card, context=small, transaction_date=TXN)
    assert res2.eligible is False
    assert res2.amount == Decimal("0")


async def test_sbi_monthly_cap(db):
    """SBI Cashback: 5% online, capped at ₹2000 per calendar month (unchanged)."""
    user = await _make_user(db)
    card = await _make_card(db, user, card_name="SBI Cashback Card", issuer="SBI")
    await _add_rule(
        db, card,
        rule_name="5% Cashback Online", reward_type=RewardType.CASHBACK,
        reward_rate=Decimal("5"), point_value=Decimal("1"),
        applies_to=RewardAppliesTo.ONLINE, monthly_cap=Decimal("2000"),
    )
    engine = get_rewards_engine()

    online = SpendContext(Decimal("50000"), "store", "", PaymentMethod.CREDIT_CARD, True)
    first = await engine.evaluate(db, user_id=user.id, card=card, context=online, transaction_date=TXN)
    assert first.amount == Decimal("2000.00")  # 5% = 2500, capped to 2000

    db.add(
        Expense(
            user_id=user.id, credit_card_id=card.id, amount=Decimal("50000"),
            category=ExpenseCategory.OTHER, payment_method=PaymentMethod.CREDIT_CARD,
            transaction_date=TXN, is_online=True, cashback_amount=first.amount,
        )
    )
    await db.flush()

    second = await engine.evaluate(db, user_id=user.id, card=card, context=online, transaction_date=TXN)
    assert second.eligible is True
    assert second.amount == Decimal("0.00")  # monthly cap exhausted


async def test_reward_points_inr_equivalent(db):
    """Points rule: units = rate * spend; ₹ value = units * point_value."""
    user = await _make_user(db)
    card = await _make_card(db, user, card_name="Premium Rewards", issuer="HDFC")
    await _add_rule(
        db, card,
        rule_name="2 points / ₹", reward_type=RewardType.REWARD_POINTS,
        reward_rate=Decimal("2"), point_value=Decimal("0.25"),
        applies_to=RewardAppliesTo.ALL,
    )
    engine = get_rewards_engine()

    ctx = SpendContext(Decimal("1000"), "anywhere", "", PaymentMethod.CREDIT_CARD, False)
    res = await engine.evaluate(db, user_id=user.id, card=card, context=ctx, transaction_date=TXN)
    assert res.eligible is True
    # 1000 * 2 = 2000 points; ₹ value = 2000 * 0.25 = 500.
    assert res.amount == Decimal("500.00")

    rules = await engine.load_rules(db, card.id)
    assert rules[0].reward_units(Decimal("1000")) == Decimal("2000.00")


async def test_category_specific_rule(db):
    """Category-specific rule only applies to its category."""
    user = await _make_user(db)
    card = await _make_card(db, user, card_name="Travel Card", issuer="Axis")
    await _add_rule(
        db, card,
        rule_name="5% on Travel", reward_type=RewardType.CASHBACK,
        reward_rate=Decimal("5"), point_value=Decimal("1"),
        applies_to=RewardAppliesTo.CATEGORY_SPECIFIC, category_match="travel",
    )
    engine = get_rewards_engine()

    travel = SpendContext(Decimal("1000"), "indigo", "", PaymentMethod.CREDIT_CARD, True, "travel")
    res = await engine.evaluate(db, user_id=user.id, card=card, context=travel, transaction_date=TXN)
    assert res.amount == Decimal("50.00")

    food = SpendContext(Decimal("1000"), "kfc", "", PaymentMethod.CREDIT_CARD, True, "food")
    res2 = await engine.evaluate(db, user_id=user.id, card=card, context=food, transaction_date=TXN)
    assert res2.eligible is False


async def test_no_card_no_cashback(db):
    user = await _make_user(db)
    engine = get_rewards_engine()
    ctx = SpendContext(Decimal("1000"), "anything", "", PaymentMethod.UPI, True)
    res = await engine.evaluate(db, user_id=user.id, card=None, context=ctx, transaction_date=TXN)
    assert res.eligible is False
    assert res.amount == Decimal("0")
