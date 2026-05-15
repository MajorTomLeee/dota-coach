from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


def build_scheduler(weekly_callback: Callable) -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    sched.add_job(
        weekly_callback,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_review",
    )
    return sched
