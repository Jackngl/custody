"""Tests for public-holiday bridge helpers (weekend custody)."""

import importlib.util
from datetime import date, datetime
from pathlib import Path

_BRIDGE = Path(__file__).resolve().parents[1] / "custom_components" / "custody_schedule" / "holiday_bridge.py"
_spec = importlib.util.spec_from_file_location("custody_holiday_bridge", _BRIDGE)
hb = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hb)


def test_easter_monday_2026_extends_end_after_sunday():
    """After a Sunday end, custody extends through Easter Monday (FR)."""
    holidays = hb.get_public_holidays(2026, "FR", False)
    assert date(2026, 4, 6) in holidays
    assert date(2026, 4, 5) not in holidays

    sunday_end = datetime(2026, 4, 5, 0, 0, 0)
    extended = hb.apply_public_holiday_bridge_after_last_day(sunday_end, holidays)
    assert extended.date() == date(2026, 4, 6)


def test_no_extension_when_next_day_not_holiday():
    holidays = hb.get_public_holidays(2026, "FR", False)
    d = datetime(2026, 1, 11, 0, 0, 0)
    extended = hb.apply_public_holiday_bridge_after_last_day(d, holidays)
    assert extended.date() == d.date()


def test_friday_labour_day_moves_weekend_start_to_thursday():
    """When weekend starts on a public holiday Friday, start moves back day by day."""
    holidays = hb.get_public_holidays(2026, "FR", False)
    assert date(2026, 5, 1) in holidays

    friday_start = datetime(2026, 5, 1, 0, 0, 0)
    shifted = hb.apply_public_holiday_bridge_before_weekend_start(friday_start, holidays)
    assert shifted.date() == date(2026, 4, 30)


def test_chained_holidays_after_last_day():
    """Consecutive holidays after end day extend multiple days."""
    holidays = {date(2026, 6, 1), date(2026, 6, 2)}
    end = datetime(2026, 5, 31, 0, 0, 0)
    extended = hb.apply_public_holiday_bridge_after_last_day(end, holidays)
    assert extended.date() == date(2026, 6, 2)
