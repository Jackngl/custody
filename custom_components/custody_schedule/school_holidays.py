"""School holiday helper for Custody Schedule."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import HOLIDAY_API, LOGGER

# The French Education Nationale dataset expresses dates as Paris local midnight
# (e.g. "2026-11-01T23:00:00+00:00" == Monday 2026-11-02 00:00 Europe/Paris).
# We anchor them to Europe/Paris so the "school resume day at 00:00" semantics
# survive regardless of the Home Assistant time zone.
FRANCE_TZ = dt_util.get_time_zone("Europe/Paris")


@dataclass(slots=True)
class SchoolHoliday:
    """Represent a school holiday period."""

    name: str
    zone: str
    start: datetime
    end: datetime


class BaseHolidayProvider(ABC):
    """Base class for school holiday providers."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession) -> None:
        self.hass = hass
        self.session = session

    @abstractmethod
    async def get_holidays(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Fetch holidays for a specific country, zone and year."""


class FranceEducationProvider(BaseHolidayProvider):
    """Provider for French school holidays using Education Nationale API."""

    def _get_school_year(self, date: datetime) -> str:
        """Convert a calendar date to school year format (e.g., '2024-2025')."""
        year = date.year
        if date.month < 9:
            return f"{year - 1}-{year}"
        return f"{year}-{year + 1}"

    def _normalize_zone(self, zone: str) -> str:
        """Normalize zone name for API compatibility."""
        zone_mapping = {
            "Corse": "Corse",
            "DOM-TOM": "Guadeloupe",
            "A": "Zone A",
            "B": "Zone B",
            "C": "Zone C",
        }
        return zone_mapping.get(zone, zone)

    async def get_holidays(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Fetch holidays from the French API."""
        now = dt_util.now()
        school_years = set()

        if year is not None:
            school_years.add(f"{year - 1}-{year}")
            school_years.add(f"{year}-{year + 1}")
        else:
            current_school_year = self._get_school_year(now)
            school_years.add(current_school_year)
            parts = current_school_year.split("-")
            if len(parts) == 2:
                next_year_start = int(parts[1])
                school_years.add(f"{next_year_start}-{next_year_start + 1}")
                school_years.add(f"{next_year_start + 1}-{next_year_start + 2}")

        normalized_zone = self._normalize_zone(zone)
        all_holidays: list[SchoolHoliday] = []

        for school_year in school_years:
            url = HOLIDAY_API.format(zone=normalized_zone, year=school_year)
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    resp.raise_for_status()
                    payload: dict[str, Any] = await resp.json()

                    records = payload.get("records", [])

                    # Manual fallback if zone filtering fails in the API
                    if len(records) == 0 and normalized_zone in ["A", "B", "C"]:
                        url_all = (
                            "https://data.education.gouv.fr/api/records/1.0/search/"
                            f"?dataset=fr-en-calendrier-scolaire"
                            f"&refine.annee_scolaire={school_year}"
                            f"&rows=100"
                        )
                        async with self.session.get(url_all) as resp2:
                            resp2.raise_for_status()
                            payload_all = await resp2.json()
                            for r in payload_all.get("records", []):
                                fields = r.get("fields", {})
                                zone_field = str(fields.get("zones") or fields.get("zone") or "")
                                if normalized_zone == zone_field or normalized_zone in zone_field.split(","):
                                    records.append(r)

                    for record in records:
                        fields = record.get("fields", {})
                        start_str = fields.get("start_date") or fields.get("date_debut")
                        end_str = fields.get("end_date") or fields.get("date_fin")
                        name = fields.get("description") or fields.get("libelle") or "Vacances scolaires"

                        if not start_str or not end_str:
                            continue

                        start = dt_util.parse_datetime(start_str)
                        end = dt_util.parse_datetime(end_str)

                        if not start or not end:
                            continue

                        if year is not None and not (
                            start.year == year or end.year == year or (start.year < year < end.year)
                        ):
                            continue

                        all_holidays.append(
                            SchoolHoliday(
                                name=name,
                                zone=zone,
                                start=start.astimezone(FRANCE_TZ) if FRANCE_TZ else dt_util.as_local(start),
                                end=end.astimezone(FRANCE_TZ) if FRANCE_TZ else dt_util.as_local(end),
                            )
                        )
            except Exception as err:
                LOGGER.error("Error fetching holidays from France provider: %s", err)

        return sorted(all_holidays, key=lambda h: (h.start, h.end))


class OpenHolidaysProvider(BaseHolidayProvider):
    """Provider for BE, CH, LU using OpenHolidays API."""

    async def get_holidays(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Fetch holidays from OpenHolidays API."""
        now = dt_util.now()
        years = [year] if year else [now.year, now.year + 1, now.year + 2]
        all_holidays = []

        for target_year in years:
            # OpenHolidays API: https://www.openholidaysapi.org/en/
            # Format: /SchoolHolidays?countryIsoCode=BE&languageIsoCode=FR&validFrom=2024-01-01&validTo=2024-12-31
            lang = "FR" if country in ["BE", "CH", "LU"] else "EN"
            valid_from = f"{target_year}-01-01"
            valid_to = f"{target_year + 1}-01-01"

            base_url = "https://openholidaysapi.org/SchoolHolidays"
            params = {
                "countryIsoCode": country,
                "languageIsoCode": lang,
                "validFrom": valid_from,
                "validTo": valid_to,
            }

            # If zone is specified (Subdivision/Group), add it (Canton for CH, Community for BE)
            if zone and zone not in ["FR", "BE", "CH", "LU", "A", "B", "C", "Corse", "DOM-TOM"]:
                if country == "BE":
                    params["groupCode"] = zone
                else:
                    params["subdivisionCode"] = zone

            try:
                async with self.session.get(base_url, params=params) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
                    for item in payload:
                        name_dict = item.get("name", [])
                        name = next((n.get("text") for n in name_dict if n.get("language") == lang.lower()), "Vacances")
                        start_naive = dt_util.parse_datetime(item.get("startDate"))
                        end_naive = dt_util.parse_datetime(item.get("endDate"))
                        if start_naive and end_naive:
                            # Use explicit combine with local timezone to prevent shifts
                            tz = dt_util.get_time_zone(self.hass.config.time_zone)
                            start = dt_util.as_local(
                                datetime.combine(start_naive.date(), datetime.min.time(), tzinfo=tz)
                            )
                            end = dt_util.as_local(datetime.combine(end_naive.date(), datetime.max.time(), tzinfo=tz))

                            all_holidays.append(
                                SchoolHoliday(
                                    name=name,
                                    zone=zone,
                                    start=start,
                                    end=end,
                                )
                            )
            except Exception as err:
                LOGGER.error("Error fetching from OpenHolidays for %s: %s", target_year, err)

        return sorted(all_holidays, key=lambda h: h.start)


class CanadaHolidayProvider(BaseHolidayProvider):
    """Provider for Canada/Quebec. Focuses on Statutory Public Holidays for now."""

    async def get_holidays(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Fetch holidays for Canada."""
        now = dt_util.now()
        years = [year] if year else [now.year, now.year + 1, now.year + 2]
        all_holidays = []
        tz = dt_util.get_time_zone(self.hass.config.time_zone)

        for target_year in years:
            url = f"https://canada-holidays.ca/api/v1/provinces/QC?year={target_year}"
            try:
                async with self.session.get(url) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
                    province = payload.get("province", {})
                    for h in province.get("holidays", []):
                        name = h.get("nameFr") or h.get("nameEn")
                        start_date = dt_util.parse_datetime(h.get("observedDate") or h.get("date"))
                        if start_date:
                            start = dt_util.as_local(
                                datetime.combine(start_date.date(), datetime.min.time(), tzinfo=tz)
                            )
                            end = dt_util.as_local(datetime.combine(start_date.date(), datetime.max.time(), tzinfo=tz))
                            all_holidays.append(SchoolHoliday(name, zone, start, end))
            except Exception as err:
                LOGGER.error("Error fetching from Canada provider for %s: %s", target_year, err)

        return sorted(all_holidays, key=lambda h: h.start)


STORAGE_VERSION = 1
STORAGE_KEY = "custody_schedule_holidays"


class SchoolHolidayClient:
    """Client that delegates to specific country providers."""

    def __init__(self, hass: HomeAssistant, api_url: str | None = None) -> None:
        self._hass = hass
        self._session = aiohttp_client.async_get_clientsession(hass)
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._cache_loaded = False
        self._cache: dict[tuple[str, str, str, int | None], dict[str, Any]] = {}
        self._france_provider = FranceEducationProvider(hass, self._session)
        self._open_provider = OpenHolidaysProvider(hass, self._session)
        self._canada_provider = CanadaHolidayProvider(hass, self._session)

    async def _async_load_cache(self) -> None:
        if self._cache_loaded:
            return
        try:
            data = await self._store.async_load()
            if data:
                for key_str, entry in data.items():
                    parts = key_str.split("|")
                    if len(parts) >= 3:
                        country, zone, year_str = parts[0], parts[1], parts[2]
                        year = int(year_str) if year_str != "None" else None
                        key = (country, zone, str(year), year)

                        # Support for both old format (list) and new format (dict with timestamp)
                        if isinstance(entry, list):
                            holidays_data = entry
                            # Force refresh by simulating an old fetch (60 days ago)
                            timestamp = (dt_util.now() - timedelta(days=60)).isoformat()
                        else:
                            holidays_data = entry.get("holidays", [])
                            timestamp = entry.get("timestamp", (dt_util.now() - timedelta(days=60)).isoformat())

                        holidays = []
                        for h in holidays_data:
                            start_dt = dt_util.parse_datetime(h.get("start", ""))
                            end_dt = dt_util.parse_datetime(h.get("end", ""))
                            if start_dt and end_dt:
                                holidays.append(
                                    SchoolHoliday(
                                        name=h.get("name", "Vacances"),
                                        zone=h.get("zone", ""),
                                        start=start_dt,
                                        end=end_dt,
                                    )
                                )
                        if holidays:
                            self._cache[key] = {"timestamp": timestamp, "holidays": holidays}
        except Exception as err:
            LOGGER.warning("Error loading holiday cache: %s", err)

        self._cache_loaded = True

    async def _async_save_cache(self) -> None:
        try:
            data = {}
            for key, cache_entry in self._cache.items():
                key_str = f"{key[0]}|{key[1]}|{key[2]}"
                data[key_str] = {
                    "timestamp": cache_entry["timestamp"],
                    "holidays": [
                        {
                            "name": h.name,
                            "zone": h.zone,
                            "start": h.start.isoformat(),
                            "end": h.end.isoformat(),
                        }
                        for h in cache_entry["holidays"]
                    ],
                }
            await self._store.async_save(data)
        except Exception as err:
            LOGGER.warning("Error saving holiday cache: %s", err)

    async def async_list(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Return holidays using the appropriate provider."""
        await self._async_load_cache()

        cache_key = (country, zone, str(year), year)
        now = dt_util.now()

        # Try to use fresh cache (< 30 days old)
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            # Parse timestamp safely
            cache_time = dt_util.parse_datetime(cache_entry["timestamp"])
            if cache_time and (now - cache_time).days < 30:
                return cache_entry["holidays"]

        if country == "FR":
            provider = self._france_provider
        elif country in ["BE", "CH", "LU"]:
            provider = self._open_provider
        elif country == "CA_QC":
            provider = self._canada_provider
        else:
            provider = self._france_provider

        try:
            holidays = await provider.get_holidays(country, zone, year)
        except Exception as err:
            LOGGER.error("Holiday provider error for %s %s: %s", country, zone, err)
            holidays = []

        if not holidays:
            # Fallback to expired cache if available ("anti-flood" / "fallback" mode)
            if cache_key in self._cache:
                LOGGER.warning(
                    "Using expired fallback cache for %s %s due to API failure or empty response", country, zone
                )
                return self._cache[cache_key]["holidays"]
            return []

        # 1. Deduplicate by name and exact dates
        seen = set()
        deduped = []
        for h in holidays:
            k = (h.name, h.start, h.end)
            if k not in seen:
                seen.add(k)
                deduped.append(h)

        # 2. Sort by start date (ascending) and duration (descending)
        # This ensures the most complete holiday is processed first for any given day
        deduped.sort(key=lambda h: (h.start, -(h.end - h.start).total_seconds()))

        # 3. Filter out duplicates for the SAME holiday (starting on the same day)
        unique_holidays = []
        if deduped:
            current = deduped[0]
            for next_h in deduped[1:]:
                # If they start on the same day, they are likely duplicates/variants
                # We already have the longest version in 'current' due to sorting
                if next_h.start.date() == current.start.date():
                    continue
                else:
                    unique_holidays.append(current)
                    current = next_h
            unique_holidays.append(current)

        self._cache[cache_key] = {"timestamp": now.isoformat(), "holidays": unique_holidays}
        self._hass.async_create_task(self._async_save_cache())
        return unique_holidays

    async def async_test_connection(self, country: str, zone: str, year: int | None = None) -> dict[str, Any]:
        """Test API connection."""
        try:
            holidays = await self.async_list(country, zone, year)
            return {
                "success": True,
                "country": country,
                "zone": zone,
                "holidays_count": len(holidays),
                "holidays": [{"name": h.name, "start": h.start.isoformat()} for h in holidays[:5]],
            }
        except Exception as err:
            return {"success": False, "error": str(err)}

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._hass.async_create_task(self._async_save_cache())
