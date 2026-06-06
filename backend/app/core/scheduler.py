"""APScheduler setup for background jobs.

Currently runs a daily notification scan across all users. The job opens its
own session (it is not request-scoped) and commits its own work.
"""

from __future__ import annotations

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services import notification_service
from app.services.insights_service import get_insight_generator
from app.services.llm import get_llm_client

logger = logging.getLogger("ledgeriq.scheduler")

scheduler = AsyncIOScheduler(timezone=settings.DEFAULT_TIMEZONE)


async def run_notification_scan() -> int:
    """Job entrypoint: scan all users and persist generated notifications."""
    async with AsyncSessionLocal() as session:
        try:
            created = await notification_service.scan_all_users(session)
            await session.commit()
            logger.info("Notification scan created %s notification(s)", created)
            return created
        except Exception:
            await session.rollback()
            logger.exception("Notification scan failed")
            raise


async def run_insight_refresh() -> int:
    """Job entrypoint: regenerate and cache LLM insights for every user."""
    generator = get_insight_generator()
    refresh = getattr(generator, "refresh", None)
    if refresh is None:
        return 0  # rule-based generator: nothing to refresh
    async with AsyncSessionLocal() as session:
        user_ids = (await session.execute(select(User.id))).scalars().all()
        for uid in user_ids:
            await refresh(
                session, uid, period=settings.LLM_INSIGHTS_PERIOD, reference=date.today()
            )
        logger.info("Refreshed LLM insights for %s user(s)", len(user_ids))
        return len(user_ids)


def start_scheduler() -> None:
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")
        return
    if scheduler.running:
        return
    scheduler.add_job(
        run_notification_scan,
        trigger=CronTrigger(hour=settings.NOTIFICATION_SCAN_HOUR, minute=0),
        id="daily_notification_scan",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(
        "Scheduler started — daily notification scan at %02d:00 %s",
        settings.NOTIFICATION_SCAN_HOUR,
        settings.DEFAULT_TIMEZONE,
    )

    # Weekly LLM insight refresh — only when an LLM key is configured.
    if settings.LLM_INSIGHTS_ENABLED and get_llm_client() is not None:
        scheduler.add_job(
            run_insight_refresh,
            trigger=CronTrigger(
                day_of_week=settings.LLM_INSIGHTS_DAY_OF_WEEK,
                hour=settings.LLM_INSIGHTS_HOUR,
                minute=0,
            ),
            id="weekly_insight_refresh",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        logger.info(
            "Scheduler — weekly LLM insight refresh (%s %02d:00)",
            settings.LLM_INSIGHTS_DAY_OF_WEEK,
            settings.LLM_INSIGHTS_HOUR,
        )

    scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
