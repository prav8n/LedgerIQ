"""APScheduler setup for background jobs.

Currently runs a daily notification scan across all users. The job opens its
own session (it is not request-scoped) and commits its own work.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services import notification_service

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
    scheduler.start()
    logger.info(
        "Scheduler started — daily notification scan at %02d:00 %s",
        settings.NOTIFICATION_SCAN_HOUR,
        settings.DEFAULT_TIMEZONE,
    )


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
