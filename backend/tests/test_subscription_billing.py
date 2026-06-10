"""Auto-posting of due subscriptions as reward-earning expenses."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.models.credit_card import CreditCard
from app.models.enums import (
    ExpenseCategory,
    Frequency,
    PaymentMethod,
    RewardAppliesTo,
    RewardType,
)
from app.models.expense import Expense
from app.models.reward_rule import RewardRule
from app.models.subscription import Subscription
from app.models.user import User
from app.services.subscription_billing import post_due_subscriptions


async def test_auto_post_due_subscription_earns_and_advances(db):
    user = User(email="sub@example.com", hashed_password=hash_password("x"))
    db.add(user)
    await db.flush()

    card = CreditCard(
        user_id=user.id, card_name="CC", issuer="HDFC",
        credit_limit=Decimal("100000"), current_balance=Decimal("0"),
    )
    db.add(card)
    await db.flush()
    db.add(
        RewardRule(
            card_id=card.id, rule_name="5%", reward_type=RewardType.CASHBACK,
            reward_rate=Decimal("5"), point_value=Decimal("1"),
            applies_to=RewardAppliesTo.ALL,
        )
    )
    await db.flush()

    sub = Subscription(
        user_id=user.id, name="Netflix", amount=Decimal("500"),
        billing_cycle=Frequency.MONTHLY, start_date=date(2026, 5, 1),
        next_billing_date=date(2026, 6, 1), payment_method=PaymentMethod.CREDIT_CARD,
        credit_card_id=card.id, auto_renew=True, is_active=True,
    )
    db.add(sub)
    await db.flush()

    posted = await post_due_subscriptions(db, today=date(2026, 6, 5))
    assert posted == 1

    expenses = (
        await db.execute(select(Expense).where(Expense.user_id == user.id))
    ).scalars().all()
    assert len(expenses) == 1
    exp = expenses[0]
    assert exp.category is ExpenseCategory.SUBSCRIPTION
    assert exp.credit_card_id == card.id
    assert exp.cashback_amount == Decimal("25.00")  # 5% of 500

    await db.refresh(card)
    assert card.current_balance == Decimal("500.00")  # outstanding raised

    await db.refresh(sub)
    assert sub.next_billing_date == date(2026, 7, 1)  # advanced one cycle


async def test_not_due_subscription_is_skipped(db):
    user = User(email="sub2@example.com", hashed_password=hash_password("x"))
    db.add(user)
    await db.flush()
    sub = Subscription(
        user_id=user.id, name="Spotify", amount=Decimal("119"),
        billing_cycle=Frequency.MONTHLY, start_date=date(2026, 6, 1),
        next_billing_date=date(2026, 7, 1), payment_method=PaymentMethod.UPI,
        auto_renew=True, is_active=True,
    )
    db.add(sub)
    await db.flush()

    posted = await post_due_subscriptions(db, today=date(2026, 6, 5))
    assert posted == 0
    count = await db.scalar(select(Expense).where(Expense.user_id == user.id))
    assert count is None
