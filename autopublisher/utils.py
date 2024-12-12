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


async def get_next_reset_timestamp(
    current_time: datetime,
    *,
    target_weekday: int = None,
    target_day: int = None,
    target_month: int = None
) -> int:
    """
    Calculate the next timestamp for a given target based on current time, weekday, day, and month.

    Parameters:
    -------------
    - current_time: The current datetime.
    - target_weekday: The target weekday (0-6, Monday-Sunday).
    - target_day: The target day of the month.
    - target_month: The target month.

    Returns:
    ---------
    - int: The next timestamp after the target date.
    """

    def is_leap_year(year):
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def days_in_month(month, year):
        if month == 2:
            return 29 if is_leap_year(year) else 28
        return 31 if month in (1, 3, 5, 7, 8, 10, 12) else 30

    if target_weekday is not None:
        delta = (target_weekday - current_time.weekday()) % 7
        if current_time.weekday() + delta > 6:
            delta -= 7
        next_target_date = current_time + timedelta(days=delta)

    elif target_day is not None and target_month is None:
        days_until = (target_day - current_time.day) % days_in_month(
            current_time.month, current_time.year
        ) or days_in_month(current_time.month, current_time.year)
        next_target_date = current_time + timedelta(days=days_until)

    elif target_day is not None and target_month is not None:
        next_year = current_time.year + (
            current_time.month > target_month
            or (current_time.month == target_month and current_time.day >= target_day)
        )
        next_target_date = datetime(next_year, target_month, target_day)

    else:
        raise ValueError(
            "Must provide either target_weekday, target_day, or both target_day and target_month"
        )

    next_target_midnight = datetime.combine(next_target_date, datetime.min.time())
    return int(next_target_midnight.timestamp())
