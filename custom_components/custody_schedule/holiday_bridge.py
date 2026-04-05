"""Public holiday helpers without Home Assistant imports (testable in isolation)."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def easter_sunday(year: int) -> date:
    """Calculate Easter Sunday date using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month = (h + L - 7 * m + 114) // 31
    day = ((h + L - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_public_holidays(year: int, country: str = "FR", include_alsace_moselle: bool = False) -> set[date]:
    """Return set of public holidays for a given year and country.

    Currently supports: France (FR).
    """
    holidays: set[date] = set()

    if country == "FR":
        holidays.add(date(year, 1, 1))
        holidays.add(date(year, 5, 1))
        holidays.add(date(year, 5, 8))
        holidays.add(date(year, 7, 14))
        holidays.add(date(year, 8, 15))
        holidays.add(date(year, 11, 1))
        holidays.add(date(year, 11, 11))
        holidays.add(date(year, 12, 25))

        if include_alsace_moselle:
            holidays.add(date(year, 12, 26))

        easter = easter_sunday(year)
        holidays.add(easter + timedelta(days=1))
        holidays.add(easter + timedelta(days=39))
        holidays.add(easter + timedelta(days=50))

        if include_alsace_moselle:
            holidays.add(easter - timedelta(days=2))

    return holidays


def apply_public_holiday_bridge_after_last_day(end_date: datetime, holidays: set[date]) -> datetime:
    """Extend custody through consecutive public holidays immediately after the last custody day.

    If custody nominally ends Sunday but Monday is a public holiday (e.g. Easter Monday in FR),
    the end moves to Monday (same time-of-day until _apply_time sets departure).
    """
    current = end_date
    while current.date() + timedelta(days=1) in holidays:
        current = current + timedelta(days=1)
    return current


def apply_public_holiday_bridge_before_weekend_start(weekend_start: datetime, holidays: set[date]) -> datetime:
    """Move weekend start earlier while the start day is a public holiday (e.g. Friday off -> Thursday)."""
    current = weekend_start
    while current.date() in holidays:
        current = current - timedelta(days=1)
    return current
