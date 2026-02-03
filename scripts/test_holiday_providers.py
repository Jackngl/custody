import asyncio
import aiohttp
from datetime import datetime
import sys
import os

# Add the component directory to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd(), "custom_components", "custody_schedule"))

# Mock Logger and Home Assistant if needed, but for now we'll just test the providers
# in a simplified way by extracting the logic if necessary or by providing enough mocks.


# Mock HomeAssistant and Logger for standalone testing
class MockHass:
    def __init__(self):
        self.data = {}


class MockLogger:
    def info(self, msg, *args):
        print(f"INFO: {msg % args if args else msg}")

    def error(self, msg, *args):
        print(f"ERROR: {msg % args if args else msg}")

    def debug(self, msg, *args):
        print(f"DEBUG: {msg % args if args else msg}")

    def warning(self, msg, *args):
        print(f"WARNING: {msg % args if args else msg}")


import custom_components.custody_schedule.school_holidays as sh
import custom_components.custody_schedule.const as const

# Monkeypatch the logger in the component
sh.LOGGER = MockLogger()


async def test_france_provider(session):
    print("\n--- Testing FranceEducationProvider ---")
    hass = MockHass()
    client = sh.SchoolHolidayClient(hass)
    holidays = await client.async_list("FR", "A", 2025)
    print(f"Found {len(holidays)} holidays for France Zone A 2025")
    for h in holidays[:3]:
        print(f"  - {h.name}: {h.start.date()} to {h.end.date()}")


async def test_openholidays_provider(session):
    print("\n--- Testing OpenHolidaysProvider (Belgium) ---")
    hass = MockHass()
    client = sh.SchoolHolidayClient(hass)
    holidays = await client.async_list("BE", "BE-BE", 2025)
    print(f"Found {len(holidays)} holidays for Belgium (FR Community) 2025")
    for h in holidays[:3]:
        print(f"  - {h.name}: {h.start.date()} to {h.end.date()}")


async def test_canada_provider(session):
    print("\n--- Testing CanadaHolidayProvider (Quebec) ---")
    hass = MockHass()
    client = sh.SchoolHolidayClient(hass)
    holidays = await client.async_list("CA_QC", "QC", 2025)
    print(f"Found {len(holidays)} holidays for Quebec 2025")
    for h in holidays[:3]:
        print(f"  - {h.name}: {h.start.date()} to {h.end.date()}")


async def main():
    async with aiohttp.ClientSession() as session:
        await test_france_provider(session)
        await test_openholidays_provider(session)
        await test_canada_provider(session)


if __name__ == "__main__":
    asyncio.run(main())
