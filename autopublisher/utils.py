from datetime import datetime, timedelta

def get_next_reset_timestamp(now, target_weekday=None, target_day=None, target_month=None):
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
        raise ValueError("Either target_weekday or target_day must be provided")

    next_target_midnight = datetime.combine(next_target, datetime.min.time())
    return int(next_target_midnight.timestamp())
