"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from red_commons.logging import getLogger
from redbot.core import Config, commands

logger = getLogger("red.maxcogs.autopublisher.utils")


async def get_owner_timezone(config: Config) -> pytz.timezone:
    """Retrieve the owner's timezone from config, default to UTC."""
    timezone_str = await config.timezone()
    try:
        tz = pytz.timezone(timezone_str)
        logger.debug(f"Retrieved timezone: {timezone_str}")
        return tz
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Invalid timezone in config: {timezone_str}, falling back to UTC")
        return pytz.UTC


async def initialize_scheduler(cog: commands.Cog) -> AsyncIOScheduler:
    """Initialize the scheduler."""
    scheduler = AsyncIOScheduler()
    try:
        logger.info("Scheduler initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
    return scheduler


async def schedule_resets(cog: commands.Cog) -> None:
    """Schedule periodic count resets in the owner's timezone."""
    owner_tz = await get_owner_timezone(cog.config)
    cog.scheduler.remove_all_jobs()
    cog.scheduler.add_job(
        reset_count,
        "cron",
        day_of_week="sun",
        hour=0,
        minute=0,
        timezone=owner_tz,
        args=[cog.config, "weekly"],
        id="weekly_reset",
    )
    cog.scheduler.add_job(
        reset_count,
        "cron",
        day=1,
        hour=0,
        minute=0,
        timezone=owner_tz,
        args=[cog.config, "monthly"],
        id="monthly_reset",
    )
    cog.scheduler.add_job(
        reset_count,
        "cron",
        month=1,
        day=1,
        hour=0,
        minute=0,
        timezone=owner_tz,
        args=[cog.config, "yearly"],
        id="yearly_reset",
    )
    if not cog.scheduler.running:
        try:
            cog.scheduler.start()
            logger.info("Scheduler started with jobs: weekly, monthly, yearly")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)


async def reset_count(config: Config, period: str) -> None:
    """Reset the specified count period."""
    async with config.all() as data:
        if period == "weekly":
            data["published_weekly_count"] = 0
            logger.info("Weekly count reset.")
        elif period == "monthly":
            data["published_monthly_count"] = 0
            logger.info("Monthly count reset.")
        elif period == "yearly":
            data["published_yearly_count"] = 0
            logger.info("Yearly count reset.")
        else:
            logger.warning(f"Unknown reset period: {period}")


async def increment_published_count(config: Config) -> None:
    """Increment all published message counts."""
    async with config.all() as data:
        for key in [
            "published_count",
            "published_weekly_count",
            "published_monthly_count",
            "published_yearly_count",
        ]:
            data[key] = data.get(key, 0) + 1
            logger.debug(f"Incremented {key}")
        data["last_count_time"] = datetime.utcnow().isoformat()


def get_next_reset_times(owner_tz: pytz.timezone) -> tuple[int, int, int]:
    """Calculate next reset timestamps, ensuring correct timezone handling."""
    now = datetime.now(owner_tz)

    # Weekly reset: Next Sunday
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour >= 0:
        days_until_sunday = 7
    next_weekly = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=days_until_sunday)
    next_weekly = owner_tz.localize(next_weekly)
    next_weekly_ts = int(next_weekly.timestamp())

    # Monthly reset: First day of next month
    next_month = datetime(
        year=now.year,
        month=now.month,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    next_month = owner_tz.localize(next_month)
    next_monthly_ts = int(next_month.timestamp())

    # Yearly reset: January 1st of next year
    next_year = now.year + 1 if now.month > 1 or (now.month == 1 and now.day > 1) else now.year
    next_yearly = datetime(
        year=next_year,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_yearly = owner_tz.localize(next_yearly)
    next_yearly_ts = int(next_yearly.timestamp())

    return next_weekly_ts, next_monthly_ts, next_yearly_ts
