"""Constants for the Custody Schedule integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

DOMAIN = "custody_schedule"
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CALENDAR,
    Platform.DEVICE_TRACKER,
]
UPDATE_INTERVAL = timedelta(minutes=15)
# API du calendrier scolaire français (data.education.gouv.fr)
# Format année scolaire: "2024-2025" (septembre à juin)
# Zones: A, B, C, Corse, Guadeloupe, Martinique, Guyane, La Réunion, Mayotte, etc.
HOLIDAY_API = (
    "https://data.education.gouv.fr/api/records/1.0/search/"
    "?dataset=fr-en-calendrier-scolaire"
    "&refine.annee_scolaire={year}"
    "&refine.zones={zone}"
    "&rows=100"
)

CONF_CHILD_NAME = "child_name"
CONF_CHILD_NAME_DISPLAY = "child_name_display"
CONF_ICON = "icon"
CONF_PHOTO = "photo"
CONF_CUSTODY_TYPE = "custody_type"
CONF_REFERENCE_YEAR = "reference_year"
CONF_REFERENCE_YEAR_CUSTODY = "reference_year_custody"
CONF_REFERENCE_YEAR_VACATIONS = "reference_year_vacations"
CONF_START_DAY = "start_day"
CONF_ARRIVAL_TIME = "arrival_time"
CONF_DEPARTURE_TIME = "departure_time"
CONF_END_DAY = "end_day"
CONF_SCHOOL_LEVEL = "school_level"
CONF_LOCATION = "location"
CONF_NOTES = "notes"
CONF_COUNTRY = "country"
CONF_ZONE = "zone"
CONF_VACATION_SPLIT_MODE = "vacation_split_mode"
CONF_SUMMER_SPLIT_MODE = "summer_split_mode"
CONF_NOTIFICATIONS = "notifications"
CONF_CALENDAR_SYNC = "calendar_sync"
CONF_CALENDAR_TARGET = "calendar_target"
CONF_CALENDAR_SYNC_DAYS = "calendar_sync_days"
CONF_CALENDAR_SYNC_INTERVAL_HOURS = "calendar_sync_interval_hours"
CONF_EXCEPTIONS = "exceptions"
CONF_EXCEPTIONS_LIST = "exceptions_list"
CONF_EXCEPTIONS_RECURRING = "exceptions_recurring"
CONF_CUSTOM_RULES = "custom_rules"
CONF_HOLIDAY_API_URL = "holiday_api_url"
CONF_ALSACE_MOSELLE = "alsace_moselle"
CONF_PARENTAL_ROLE = "parental_role"
CONF_AUTO_PARENT_DAYS = "auto_parent_days"
CONF_CUSTOM_PATTERN = "custom_pattern"

# Modular features (custody can be disabled for vacations-only mode)
CONF_ENABLE_CUSTODY = "enable_custody"

# Weekend start day (for alternate_weekend custody type)
CONF_WEEKEND_START_DAY = "weekend_start_day"  # "friday" or "saturday"

SERVICE_EXPORT_PLANNING_PDF = "export_planning_pdf"

DEFAULT_COUNTRY = "FR"
COUNTRIES = ["FR", "BE", "CH", "LU", "CA_QC"]

REFERENCE_YEARS = ["even", "odd"]
VACATION_SPLIT_MODES = ["odd_first", "odd_second"]

# Zones étendues avec libellés pour l'UI
FRENCH_ZONES = ["A", "B", "C", "Corse", "DOM-TOM"]
FRENCH_ZONES_WITH_CITIES: dict[str, str] = {
    "A": "Zone A — Besançon, Bordeaux, Clermont-Ferrand, Dijon, Grenoble, Limoges, Lyon, Poitiers",
    "B": (
        "Zone B — Aix-Marseille, Amiens, Lille, Nancy-Metz, Nantes, Nice, "
        "Normandie, Orléans-Tours, Reims, Rennes, Strasbourg"
    ),
    "C": "Zone C — Créteil, Montpellier, Paris, Toulouse, Versailles",
    "Corse": "Corse",
    "DOM-TOM": "DOM-TOM",
}

# Subdivisions pour les autres pays (OpenHolidays API codes)
SUBDIVISIONS: dict[str, dict[str, str]] = {
    "BE": {
        "FR": "Communauté française",
        "NL": "Vlaamse Gemeenschap",
        "DE": "Deutschsprachige Gemeinschaft",
    },
    "CH": {
        "CH-GE": "Genève",
        "CH-VD": "Vaud",
        "CH-VS": "Valais",
        "CH-NE": "Neuchâtel",
        "CH-FR": "Fribourg",
        "CH-JU": "Jura",
        "CH-BE": "Berne",
        "CH-ZH": "Zurich",
        # ... autres cantons peuvent être ajoutés
    },
    "LU": {
        "LU": "Luxembourg (National)",
    },
    "CA_QC": {
        "QC": "Québec (Général)",
    },
}


CUSTODY_TYPES = {
    "alternate_week": {
        "label": "Semaines alternées (1/1)",
        "cycle_days": 14,
        "pattern": [
            {"days": 7, "state": "on"},
            {"days": 7, "state": "off"},
        ],
    },
    "alternate_week_parity": {
        "label": "Semaines alternées",
        "cycle_days": 7,
        "pattern": [],
    },
    "alternate_weekend": {
        "label": "Week-ends alternés",
        "cycle_days": 7,
        "pattern": [],
    },
    "two_two_three": {
        "label": "2-2-3",
        "cycle_days": 7,
        "pattern": [
            {"days": 2, "state": "on"},
            {"days": 2, "state": "off"},
            {"days": 3, "state": "on"},
        ],
    },
    "two_two_five_five": {
        "label": "2-2-5-5",
        "cycle_days": 14,
        "pattern": [
            {"days": 2, "state": "on"},
            {"days": 2, "state": "off"},
            {"days": 5, "state": "on"},
            {"days": 5, "state": "off"},
        ],
    },
    "custom": {
        "label": "Custom",
        "cycle_days": 14,
        "pattern": [],
    },
}

ATTR_NEXT_ARRIVAL = "next_arrival"
ATTR_NEXT_DEPARTURE = "next_departure"
ATTR_CUSTODY_TYPE = "custody_type"
ATTR_CURRENT_PERIOD = "current_period"
ATTR_VACATION_NAME = "vacation_name"
ATTR_NEXT_VACATION_NAME = "next_vacation_name"
ATTR_NEXT_VACATION_START = "next_vacation_start"
ATTR_NEXT_VACATION_END = "next_vacation_end"
ATTR_DAYS_UNTIL_VACATION = "days_until_vacation"
ATTR_SCHOOL_HOLIDAYS_RAW = "school_holidays_raw"
ATTR_ZONE = "zone"
ATTR_LOCATION = "location"
ATTR_NOTES = "notes"
ATTR_DAYS_REMAINING = "days_remaining"

SERVICE_SET_MANUAL_DATES = "set_manual_dates"
SERVICE_OVERRIDE_PRESENCE = "override_presence"
SERVICE_REFRESH_SCHEDULE = "refresh_schedule"
SERVICE_TEST_HOLIDAY_API = "test_holiday_api"
SERVICE_EXPORT_EXCEPTIONS = "export_exceptions"
SERVICE_IMPORT_EXCEPTIONS = "import_exceptions"
SERVICE_PURGE_CALENDAR = "purge_calendar_events"
