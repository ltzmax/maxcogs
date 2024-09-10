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

import logging
from datetime import datetime, timedelta

log = logging.getLogger("red.maxcogs.autopublisher.utils")


async def get_next_reset_timestamp(now, target_weekday=None, target_day=None, target_month=None):
    """
    Calculate the next timestamp for a given target now, weekday, day, and month.

    __Parameters__:
    -------------
    - now (datetime): The current datetime.
    - target_weekday (int): The target weekday (0-6, Monday-Sunday).
    - target_day (int): The target day of the month.
    - target_month (int): The target month.

    __Returns__:
    ---------
    - int: The next timestamp after the target date.
    """
    if target_weekday is not None:
        days_until_target = (target_weekday - now.weekday()) % 7
        if days_until_target == 0:
            days_until_target = 7
        next_target = now + timedelta(days=days_until_target)
    elif target_day is not None and target_month is None:
        days_until_target = (target_day - now.day) % 30
        if days_until_target == 0:
            days_until_target = 30
        next_target = now + timedelta(days=days_until_target)
    elif target_day is not None and target_month is not None:
        if now.month > target_month or (now.month == target_month and now.day >= target_day):
            next_year = now.year + 1
        else:
            next_year = now.year
        next_target = datetime(next_year, target_month, target_day)
    else:
        raise ValueError(
            "Must provide either target_weekday, target_day, or both target_day and target_month"
        )
        log.error(
            "Must provide either target_weekday, target_day, or both target_day and target_month"
        )

    next_target_midnight = datetime.combine(next_target, datetime.min.time())
    return int(next_target_midnight.timestamp())
