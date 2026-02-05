import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from custom_components.custody_schedule.schedule import CustodyScheduleManager


class MockHolidays:
    async def async_list(self, country, zone):
        return []


class TestCustodyLogic(unittest.TestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.hass.config.time_zone = "UTC"
        self.holidays = MockHolidays()

    def test_calculate_end_date_sunday_default(self):
        # Using string keys to avoid direct constant dependency in tests
        config = {"arrival_time": "08:00", "departure_time": "19:00", "end_day": "sunday"}
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Friday Oct 3, 2025
        start_date = datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc)
        holidays = set()

        end_date = manager._calculate_end_date(start_date, holidays)

        # Should be Sunday Oct 5, 2025
        self.assertEqual(end_date.date(), date(2025, 10, 5))
        self.assertEqual(end_date.weekday(), 6)  # Sunday

    def test_calculate_end_date_monday_return(self):
        config = {"arrival_time": "08:00", "departure_time": "19:00", "end_day": "monday"}
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Friday Oct 3, 2025
        start_date = datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc)
        holidays = set()

        end_date = manager._calculate_end_date(start_date, holidays)

        # Should be Monday Oct 6, 2025
        self.assertEqual(end_date.date(), date(2025, 10, 6))
        self.assertEqual(end_date.weekday(), 0)  # Monday

    def test_calculate_end_date_holiday_extension(self):
        config = {"arrival_time": "08:00", "departure_time": "19:00", "end_day": "monday"}
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Friday Oct 3, 2025
        start_date = datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc)
        # Monday Oct 6 is a holiday
        holidays = {date(2025, 10, 6)}

        end_date = manager._calculate_end_date(start_date, holidays)

        # Should be Tuesday Oct 7, 2025
        self.assertEqual(end_date.date(), date(2025, 10, 7))
        self.assertEqual(end_date.weekday(), 1)  # Tuesday

    def test_calculate_end_date_long_holiday_extension(self):
        config = {"arrival_time": "08:00", "departure_time": "19:00", "end_day": "monday"}
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Friday Oct 3, 2025
        start_date = datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc)
        # Monday Oct 6 and Tuesday Oct 7 are holidays
        holidays = {date(2025, 10, 6), date(2025, 10, 7)}

        end_date = manager._calculate_end_date(start_date, holidays)

        # Should be Wednesday Oct 8, 2025
        self.assertEqual(end_date.date(), date(2025, 10, 8))
        self.assertEqual(end_date.weekday(), 2)  # Wednesday

    def test_alternate_week_monday_to_monday(self):
        config = {"arrival_time": "08:00", "departure_time": "19:00", "end_day": "monday"}
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Monday Oct 6, 2025
        start_date = datetime(2025, 10, 6, 8, 0, tzinfo=timezone.utc)
        holidays = set()

        end_date = manager._calculate_end_date(start_date, holidays)

        # Should be Monday Oct 13, 2025 (7 days later)
        self.assertEqual(end_date.date(), date(2025, 10, 13))
        self.assertEqual((end_date - start_date).days, 7)

    def test_two_two_three_pattern(self):
        # 2-2-3 pattern starts with 2 days ON
        config = {
            "arrival_time": "08:00",
            "departure_time": "19:00",
            "custody_type": "two_two_three",
        }
        manager = CustodyScheduleManager(self.hass, config, self.holidays)

        # Friday Oct 3, 2025
        now = datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc)

        # This calls the general loop which uses _reference_start (returns aware)
        windows = manager._generate_pattern_windows(now)

        self.assertTrue(len(windows) > 0)
        # First window should be 2 days (index 0 and 1) -> start Friday, end Saturday
        # because duration = days-1 = 1 day. (Friday 08:00 to Saturday 19:00)
        self.assertEqual(windows[0].start.date(), date(2025, 10, 3))
        self.assertEqual(windows[0].end.date(), date(2025, 10, 4))


if __name__ == "__main__":
    unittest.main()
