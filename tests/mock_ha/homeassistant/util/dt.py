from datetime import datetime, timezone, timedelta
import zoneinfo

UTC = timezone.utc
DEFAULT_TIME_ZONE = timezone.utc

def now():
    return datetime.now(timezone.utc)

def as_local(dt):
    if dt.tzinfo is not None:
        return dt.astimezone(DEFAULT_TIME_ZONE)
    # Simulate HA: naive is treated as UTC, then converted to local
    utc_dt = dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(DEFAULT_TIME_ZONE)

def as_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def parse_datetime(dt_str):
    try:
        if not dt_str:
            return None
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None

def parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        return None

def get_time_zone(tz_str):
    try:
        return zoneinfo.ZoneInfo(tz_str)
    except Exception:
        return timezone.utc

def start_of_local_day(dt=None):
    if dt is None:
        dt = now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
