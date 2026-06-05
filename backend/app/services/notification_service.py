"""Notification generation.

Scans a user's finances and creates notifications for: upcoming EMI due dates,
upcoming subscription renewals, exceeded budgets, and goal milestones.

Deduplication is by ``(user_id, title)`` — titles embed the relevant date or
milestone so each new cycle/milestone produces exactly one notification.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.budget import Budget
from app.models.emi import EMI
from app.models.enums import NotificationCategory, NotificationType
from app.models.goal import Goal
from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.user import User
from app.services import budget_service, goal_service

_GOAL_MILESTONES = [100, 75, 50, 25]


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    message: str,
    type_: NotificationType,
    category: NotificationCategory,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    action_url: str | None = None,
) -> Notification | None:
    """Create a notification, skipping if an identical title already exists."""
    exists = await db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id, Notification.title == title
        )
    )
    if exists is not None:
        return None
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type_,
        category=category,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        action_url=action_url,
    )
    db.add(notif)
    return notif


async def scan_user(
    db: AsyncSession, user_id: int, *, today: date | None = None
) -> int:
    """Generate notifications for one user. Returns the number created."""
    today = today or date.today()
    horizon = today + timedelta(days=settings.EMI_DUE_REMINDER_DAYS)
    created = 0

    # --- EMI due soon ---
    emis = (
        await db.execute(
            select(EMI).where(
                EMI.user_id == user_id,
                EMI.is_active.is_(True),
                EMI.next_due_date <= horizon,
                EMI.next_due_date >= today,
            )
        )
    ).scalars().all()
    for emi in emis:
        n = await create_notification(
            db,
            user_id=user_id,
            title=f"EMI '{emi.loan_name}' due on {emi.next_due_date.isoformat()}",
            message=f"Your EMI of ₹{emi.emi_amount} for {emi.loan_name} is due on "
            f"{emi.next_due_date.isoformat()}.",
            type_=NotificationType.REMINDER,
            category=NotificationCategory.EMI,
            related_entity_type="emi",
            related_entity_id=emi.id,
        )
        created += n is not None

    # --- Subscription renewals (respecting each sub's reminder_days) ---
    subs = (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalars().all()
    for sub in subs:
        remind_from = sub.next_billing_date - timedelta(days=sub.reminder_days)
        if remind_from <= today <= sub.next_billing_date:
            n = await create_notification(
                db,
                user_id=user_id,
                title=f"'{sub.name}' renews on {sub.next_billing_date.isoformat()}",
                message=f"{sub.name} (₹{sub.amount}) renews on "
                f"{sub.next_billing_date.isoformat()}.",
                type_=NotificationType.REMINDER,
                category=NotificationCategory.SUBSCRIPTION,
                related_entity_type="subscription",
                related_entity_id=sub.id,
            )
            created += n is not None

    # --- Budgets exceeded (>= 100% of the current period) ---
    budgets = (
        await db.execute(
            select(Budget).where(
                Budget.user_id == user_id, Budget.is_active.is_(True)
            )
        )
    ).scalars().all()
    for budget in budgets:
        spent = await budget_service.compute_spent(db, budget, today=today)
        _, pct, st = budget_service.metrics(budget.amount, spent)
        if st == "red":
            n = await create_notification(
                db,
                user_id=user_id,
                title=f"Budget exceeded: {budget.category.value} "
                f"({today.year}-{today.month:02d})",
                message=f"You've spent ₹{spent} of your ₹{budget.amount} "
                f"{budget.category.value} budget ({pct:.0f}%).",
                type_=NotificationType.ALERT,
                category=NotificationCategory.BUDGET,
                related_entity_type="budget",
                related_entity_id=budget.id,
            )
            created += n is not None

    # --- Goal milestones (highest reached threshold) ---
    goals = (
        await db.execute(
            select(Goal).where(Goal.user_id == user_id)
        )
    ).scalars().all()
    for goal in goals:
        pct = goal_service.progress_percent(goal)
        milestone = next((m for m in _GOAL_MILESTONES if pct >= m), None)
        if milestone is None:
            continue
        n = await create_notification(
            db,
            user_id=user_id,
            title=f"Goal '{goal.name}' reached {milestone}%",
            message=f"Great progress! '{goal.name}' is at {pct:.0f}% "
            f"(₹{goal.current_amount} of ₹{goal.target_amount}).",
            type_=NotificationType.SUCCESS,
            category=NotificationCategory.GOAL,
            related_entity_type="goal",
            related_entity_id=goal.id,
        )
        created += n is not None

    await db.flush()
    return created


async def scan_all_users(db: AsyncSession, *, today: date | None = None) -> int:
    """Run ``scan_user`` for every user. Returns total notifications created."""
    user_ids = (await db.execute(select(User.id))).scalars().all()
    total = 0
    for uid in user_ids:
        total += await scan_user(db, uid, today=today)
    return total
