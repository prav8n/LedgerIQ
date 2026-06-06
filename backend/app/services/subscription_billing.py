"""Auto-posting of due subscriptions as expenses.

A scheduled job calls :func:`post_due_subscriptions` daily. For every active,
auto-renewing subscription whose ``next_billing_date`` has arrived, it creates a
``subscription`` expense — linked to the card (so it earns that card's rewards
and raises its outstanding balance) — recomputes the month's summary, and
advances the billing date to the next cycle. The per-subscription loop catches
up missed cycles (capped) so a gap in running the job self-heals.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard
from app.models.enums import ExpenseCategory
from app.models.expense import Expense
from app.models.subscription import Subscription
from app.services import subscription_service
from app.services.rewards_engine import SpendContext, get_rewards_engine
from app.services.summary_service import get_summary_service

_MAX_CATCHUP = 24  # safety cap on cycles posted per subscription per run


async def _post_charge(db: AsyncSession, sub: Subscription, billing_date: date) -> None:
    card: CreditCard | None = None
    if sub.credit_card_id is not None:
        card = await db.get(CreditCard, sub.credit_card_id)
        if card is not None and card.user_id != sub.user_id:
            card = None

    expense = Expense(
        user_id=sub.user_id,
        amount=sub.amount,
        category=ExpenseCategory.SUBSCRIPTION,
        merchant=sub.name,
        description=f"{sub.name} subscription",
        payment_method=sub.payment_method,
        transaction_date=billing_date,
        credit_card_id=card.id if card else None,
        reward_rule_id=sub.reward_rule_id if card else None,
        is_online=True,
        is_recurring=True,
        is_ai_categorized=False,
    )
    db.add(expense)
    await db.flush()

    context = SpendContext(
        amount=Decimal(str(expense.amount)),
        merchant=(expense.merchant or "").lower(),
        description=(expense.description or "").lower(),
        payment_method=expense.payment_method,
        is_online=expense.is_online,
        category=ExpenseCategory.SUBSCRIPTION.value,
    )
    result = await get_rewards_engine().evaluate(
        db,
        user_id=sub.user_id,
        card=card,
        context=context,
        transaction_date=billing_date,
        chosen_rule_id=expense.reward_rule_id,
    )
    expense.cashback_eligible = result.eligible
    expense.cashback_amount = result.amount
    expense.cashback_type = result.reward_type
    expense.cashback_rule = result.rule_id

    if card is not None:
        new_balance = Decimal(str(card.current_balance)) + Decimal(str(expense.amount))
        card.current_balance = new_balance if new_balance > 0 else Decimal("0")


async def post_due_subscriptions(db: AsyncSession, *, today: date | None = None) -> int:
    """Post expenses for every subscription due on/before ``today``. Returns count."""
    today = today or date.today()
    subs = (
        await db.execute(
            select(Subscription).where(
                Subscription.is_active.is_(True),
                Subscription.auto_renew.is_(True),
                Subscription.next_billing_date <= today,
            )
        )
    ).scalars().all()

    summary = get_summary_service()
    posted = 0
    for sub in subs:
        guard = 0
        while sub.next_billing_date <= today and guard < _MAX_CATCHUP:
            billing_date = sub.next_billing_date
            await _post_charge(db, sub, billing_date)
            await summary.recompute_month(
                db, user_id=sub.user_id, year=billing_date.year, month=billing_date.month
            )
            sub.next_billing_date = subscription_service.advance_renewal(sub)
            await db.flush()
            posted += 1
            guard += 1
    return posted
