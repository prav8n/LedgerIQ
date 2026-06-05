"""Unit tests for the cashback engine: rule matching, qualification, caps."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.security import hash_password
from app.models.credit_card import CreditCard
from app.models.enums import ExpenseCategory, PaymentMethod
from app.models.expense import Expense
from app.models.user import User
from app.services.cashback_engine import (
    SpendContext,
    get_cashback_engine,
    match_rule,
)

TXN = date(2026, 6, 10)


def test_rule_matching_by_card():
    assert match_rule(CreditCard(card_name="SBI Cashback Card", issuer="SBI")).id == "sbi_cashback_online"
    assert match_rule(CreditCard(card_name="Amazon Pay ICICI", issuer="ICICI")).id == "amazon_icici"
    assert match_rule(CreditCard(card_name="Swiggy HDFC", issuer="HDFC")).id == "swiggy_hdfc"
    assert match_rule(CreditCard(card_name="Random Card", issuer="XYZ")) is None


async def _make_user(db) -> User:
    user = User(email="cb@example.com", hashed_password=hash_password("x"))
    db.add(user)
    await db.flush()
    return user


async def test_swiggy_threshold(db):
    """Swiggy HDFC earns 10% only on orders >= ₹249."""
    user = await _make_user(db)
    card = CreditCard(user_id=user.id, card_name="Swiggy HDFC", issuer="HDFC")
    db.add(card)
    await db.flush()
    engine = get_cashback_engine()

    qualifying = SpendContext(Decimal("300"), "swiggy", "", PaymentMethod.CREDIT_CARD, False)
    res = await engine.evaluate(db, user_id=user.id, card=card, context=qualifying, transaction_date=TXN)
    assert res.eligible is True
    assert res.amount == Decimal("30.00")  # 10% of 300

    too_small = SpendContext(Decimal("200"), "swiggy", "", PaymentMethod.CREDIT_CARD, False)
    res2 = await engine.evaluate(db, user_id=user.id, card=card, context=too_small, transaction_date=TXN)
    assert res2.eligible is False
    assert res2.amount == Decimal("0")


async def test_sbi_monthly_cap(db):
    """SBI Cashback: 5% online, capped at ₹2000 per calendar month."""
    user = await _make_user(db)
    card = CreditCard(user_id=user.id, card_name="SBI Cashback Card", issuer="SBI")
    db.add(card)
    await db.flush()
    engine = get_cashback_engine()

    online = SpendContext(Decimal("50000"), "store", "", PaymentMethod.CREDIT_CARD, True)
    first = await engine.evaluate(db, user_id=user.id, card=card, context=online, transaction_date=TXN)
    assert first.amount == Decimal("2000.00")  # 5% = 2500, capped to 2000

    # Persist that cashback so the cap is considered "used".
    db.add(
        Expense(
            user_id=user.id,
            credit_card_id=card.id,
            amount=Decimal("50000"),
            category=ExpenseCategory.OTHER,
            payment_method=PaymentMethod.CREDIT_CARD,
            transaction_date=TXN,
            is_online=True,
            cashback_amount=first.amount,
        )
    )
    await db.flush()

    second = await engine.evaluate(db, user_id=user.id, card=card, context=online, transaction_date=TXN)
    assert second.eligible is True  # the spend still qualifies
    assert second.amount == Decimal("0.00")  # but the monthly cap is exhausted


async def test_no_card_no_cashback(db):
    user = await _make_user(db)
    engine = get_cashback_engine()
    ctx = SpendContext(Decimal("1000"), "anything", "", PaymentMethod.UPI, True)
    res = await engine.evaluate(db, user_id=user.id, card=None, context=ctx, transaction_date=TXN)
    assert res.eligible is False
    assert res.amount == Decimal("0")
