"""School holiday helper for Custody Schedule."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.util import dt as dt_util

from .const import HOLIDAY_API, LOGGER


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
                                start=dt_util.as_local(start),
                                end=dt_util.as_local(end),
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
        years = [year] if year else [now.year, now.year + 1]
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

            # If zone is specified (Subdivision), add it (Canton for CH, Community for BE)
            if zone and zone not in ["FR", "BE", "CH", "LU", "A", "B", "C", "Corse", "DOM-TOM"]:
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
        years = [year] if year else [now.year, now.year + 1]
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


class SchoolHolidayClient:
    """Client that delegates to specific country providers."""

    def __init__(self, hass: HomeAssistant, api_url: str | None = None) -> None:
        self._hass = hass
        self._session = aiohttp_client.async_get_clientsession(hass)
        self._cache: dict[tuple[str, str, str, int | None], list[SchoolHoliday]] = {}
        self._france_provider = FranceEducationProvider(hass, self._session)
        self._open_provider = OpenHolidaysProvider(hass, self._session)
        self._canada_provider = CanadaHolidayProvider(hass, self._session)

    async def async_list(self, country: str, zone: str, year: int | None = None) -> list[SchoolHoliday]:
        """Return holidays using the appropriate provider."""
        cache_key = (country, zone, str(year), year)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if country == "FR":
            provider = self._france_provider
        elif country in ["BE", "CH", "LU"]:
            provider = self._open_provider
        elif country == "CA_QC":
            provider = self._canada_provider
        else:
            provider = self._france_provider

        holidays = await provider.get_holidays(country, zone, year)

        # Deduplicate
        seen = set()
        unique = []
        for h in holidays:
            k = (h.name, h.start, h.end)
            if k not in seen:
                seen.add(k)
                unique.append(h)

        self._cache[cache_key] = unique
        return unique

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
