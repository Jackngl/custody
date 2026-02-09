from datetime import datetime, timedelta, timezone

UTC = timezone.utc
DEFAULT_TIME_ZONE = timezone.utc


def now():
    return datetime.now(timezone.utc)


def as_local(dt):
    return dt


def as_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_datetime(dt_str):
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def get_time_zone(tz_str):
    return timezone.utc


def start_of_local_day(dt=None):
    if dt is None:
        dt = now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
