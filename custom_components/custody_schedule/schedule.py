"""Schedule helpers for the Custody Schedule integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


def _easter_date(year: int) -> date:
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
    holidays = set()

    if country == "FR":
        # Fixed holidays
        holidays.add(date(year, 1, 1))  # New Year
        holidays.add(date(year, 5, 1))  # Labor Day
        holidays.add(date(year, 5, 8))  # Victory 1945
        holidays.add(date(year, 7, 14))  # National Day
        holidays.add(date(year, 8, 15))  # Assumption
        holidays.add(date(year, 11, 1))  # All Saints
        holidays.add(date(year, 11, 11))  # Armistice
        holidays.add(date(year, 12, 25))  # Christmas

        # Alsace-Moselle specific
        if include_alsace_moselle:
            holidays.add(date(year, 12, 26))

        # Variable
        easter = _easter_date(year)
        holidays.add(easter + timedelta(days=1))  # Easter Monday
        holidays.add(easter + timedelta(days=39))  # Ascension
        holidays.add(easter + timedelta(days=50))  # Pentecost Monday

        if include_alsace_moselle:
            holidays.add(easter - timedelta(days=2))  # Good Friday

    return holidays


def get_parent_days(year: int, country: str = "FR") -> dict[str, date]:
    """Calculate parent holidays (Mother/Father days).

    Currently supports: France (FR).
    """
    # Father's day: 3rd Sunday of June
    first_june = date(year, 6, 1)
    days_to_first_sunday = (6 - first_june.weekday()) % 7
    fathers_day = first_june + timedelta(days=days_to_first_sunday + 14)

    # Mother's day: Last Sunday of May.
    last_may = date(year, 5, 31)
    days_back_to_sunday = (last_may.weekday() - 6) % 7
    mothers_day = last_may - timedelta(days=days_back_to_sunday)

    # Check for Pentecost (Easter + 49 days)
    # Re-using logic to calculate Easter locally
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
    easter_sunday = date(year, month, day)

    pentecost_sunday = easter_sunday + timedelta(days=49)
    if mothers_day == pentecost_sunday:
        mothers_day = mothers_day + timedelta(days=7)

    return {"mother": mothers_day, "father": fathers_day}


from .const import (
    ATTR_LOCATION,
    ATTR_NOTES,
    ATTR_ZONE,
    CONF_ALSACE_MOSELLE,
    CONF_ARRIVAL_TIME,
    CONF_AUTO_PARENT_DAYS,
    CONF_COUNTRY,
    CONF_CUSTODY_TYPE,
    CONF_CUSTOM_PATTERN,
    CONF_CUSTOM_RULES,
    CONF_DEPARTURE_TIME,
    CONF_ENABLE_CUSTODY,
    CONF_END_DAY,
    CONF_EXCEPTIONS_RECURRING,
    CONF_LOCATION,
    CONF_NOTES,
    CONF_PARENTAL_ROLE,
    CONF_REFERENCE_YEAR,
    CONF_REFERENCE_YEAR_CUSTODY,
    CONF_START_DAY,
    CONF_SUMMER_SPLIT_MODE,
    CONF_VACATION_SPLIT_MODE,
    CONF_WEEKEND_START_DAY,
    CONF_ZONE,
    CUSTODY_TYPES,
    DEFAULT_COUNTRY,
    LOGGER,
)
from .school_holidays import SchoolHolidayClient


@dataclass(slots=True)
class CustodyWindow:
    """Window representing when the child is present."""

    start: datetime
    end: datetime
    label: str
    source: str = "pattern"


@dataclass(slots=True)
class CustodyComputation:
    """Final state consumed by entities."""

    is_present: bool
    next_arrival: datetime | None = None
    next_arrival_label: str | None = None
    next_departure: datetime | None = None
    next_departure_label: str | None = None
    days_remaining: int | None = None
    current_period: str = "school"
    vacation_name: str | None = None
    next_vacation_name: str | None = None
    next_vacation_start: datetime | None = None
    next_vacation_end: datetime | None = None
    days_until_vacation: int | None = None
    school_holidays_raw: list[dict[str, Any]] = field(default_factory=list)
    windows: list[CustodyWindow] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


WEEKDAY_LOOKUP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class CustodyScheduleManager:
    """Encapsulate schedule calculations and overrides."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], holidays: SchoolHolidayClient) -> None:
        self._hass = hass
        self._config = config
        self._holidays = holidays
        self._manual_windows: list[CustodyWindow] = []
        self._presence_override: dict[str, Any] | None = None
        self._tz = dt_util.get_time_zone(str(hass.config.time_zone))

        self._arrival_time = self._parse_time(config.get(CONF_ARRIVAL_TIME, "08:00"))
        self._departure_time = self._parse_time(config.get(CONF_DEPARTURE_TIME, "19:00"))
        self._end_day = config.get(CONF_END_DAY, "sunday").lower()

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update stored config (used when options change)."""
        self._config = {**self._config, **new_config}
        self._arrival_time = self._parse_time(self._config.get(CONF_ARRIVAL_TIME, "08:00"))
        self._departure_time = self._parse_time(self._config.get(CONF_DEPARTURE_TIME, "19:00"))
        self._end_day = self._config.get(CONF_END_DAY, "sunday").lower()

    def _apply_holiday_extension(self, end_date: datetime, holidays: set[date]) -> datetime:
        """Extend the end date if it falls on a holiday."""
        current_end = end_date
        while current_end.date() in holidays:
            current_end += timedelta(days=1)
        return current_end

    def _calculate_end_date(self, start_date: datetime, holidays: set[date]) -> datetime:
        """Calculate the end date based on start_date, configured end_day and holidays."""
        target_end_weekday = WEEKDAY_LOOKUP.get(self._end_day, 6)  # Default Sunday

        # Calculate days until the target weekday
        days_to_end = (target_end_weekday - start_date.weekday()) % 7

        # Special case: if end_day is same as start_day (e.g. Monday to Monday)
        # we want a full week, not 0 days.
        if days_to_end == 0 and self._end_day != "sunday":
            days_to_end = 7
        elif days_to_end == 0 and start_date.weekday() == 4:  # Friday to Friday?
            days_to_end = 7

        end_date = start_date + timedelta(days=days_to_end)
        return self._apply_holiday_extension(end_date, holidays)

    def set_manual_windows(self, ranges: Iterable[dict[str, Any]]) -> None:
        """Store manual presence windows defined via service."""
        windows: list[CustodyWindow] = []
        for rng in ranges:
            start_val = rng.get("start")
            end_val = rng.get("end")
            start = start_val if isinstance(start_val, datetime) else dt_util.parse_datetime(start_val)
            end = end_val if isinstance(end_val, datetime) else dt_util.parse_datetime(end_val)
            label = rng.get("label", "Manual custody")
            if not start or not end or end <= start:
                continue
            windows.append(
                CustodyWindow(
                    start=dt_util.as_local(start),
                    end=dt_util.as_local(end),
                    label=label,
                    source="manual",
                )
            )
        self._manual_windows = windows

    def override_presence(self, state: str, duration: timedelta | None = None) -> None:
        """Force the presence state for an optional duration."""
        now = dt_util.now()
        until = now + duration if duration else None
        self._presence_override = {"state": state, "until": until}

    def clear_override(self) -> None:
        """Remove manual override."""
        self._presence_override = None

    async def async_calculate(self, now: datetime) -> CustodyComputation:
        """Build the schedule state used by entities."""
        # now is already in local time (from dt_util.now()), no need to convert
        now_local = now if now.tzinfo else dt_util.as_local(now)
        windows = await self._build_windows(now_local)
        windows.extend(self._manual_windows)
        windows.extend(self._build_recurring_windows(now_local))
        windows.sort(key=lambda window: window.start)

        # Conserver toutes les fenêtres pour l'affichage (historique)
        all_windows = list(windows)

        # Filtrer STRICTEMENT les fenêtres qui se terminent dans le passé pour les CALCULS d'état
        # Ne garder que les fenêtres qui se terminent APRÈS maintenant (pas égal, pas proche)
        # Ajouter une marge de 1 minute pour éviter les problèmes de timing
        windows = [w for w in windows if w.end > now_local + timedelta(minutes=1)]

        # current_window : fenêtre qui commence avant ou à maintenant et se termine après maintenant
        # Mais exclure les fenêtres qui se terminent dans moins d'1 minute (considérées comme terminées)
        current_window = next(
            (
                window
                for window in windows
                if window.start <= now_local < window.end and window.end > now_local + timedelta(minutes=1)
            ),
            None,
        )
        # next_window doit être une fenêtre qui commence dans le futur ET qui se termine dans le futur
        next_window = next((window for window in windows if window.start > now_local and window.end > now_local), None)

        override_state = self._evaluate_override(now_local)

        # Check if custody management is enabled
        if not self._config.get(CONF_ENABLE_CUSTODY, True):
            # Full Custody Mode (Vacations Only)
            # Default to Present unless manually overridden to Absent
            is_present = True
            if override_state is False:
                is_present = False

            # No scheduled movements in full custody
            next_arrival = None
            next_departure = None
            days_remaining = None

            # Determine current period (still useful)
            period, vacation_name = await self._determine_period(now_local)
        else:
            # Standard Custody Management
            is_present = override_state if override_state is not None else current_window is not None

            # Si current_window existe mais se termine très bientôt (déjà filtré à la ligne 184, mais sécurité supplémentaire)
            # forcer is_present à False pour éviter d'afficher une date de départ dans le passé ou très proche
            if current_window and current_window.end <= now_local + timedelta(minutes=1):
                # La fenêtre se termine dans moins d'1 minute, considérer que l'enfant n'est plus en garde
                if override_state is None:
                    is_present = False
                    current_window = None

            next_arrival = None
            next_arrival_label = None
            next_departure = None
            next_departure_label = None
            if is_present:
                # En garde actuellement
                if current_window:
                    # On est dans une vraie fenêtre de garde
                    next_departure = current_window.end
                    next_departure_label = current_window.label
                    # S'assurer que next_departure est dans le futur (avec une marge de 1 minute)
                    if next_departure and next_departure > now_local + timedelta(minutes=1):
                        # Chercher la fenêtre qui commence après next_departure
                        next_arrival_win = next((w for w in windows if w.start > next_departure), None)
                        if next_arrival_win:
                            next_arrival = next_arrival_win.start
                            next_arrival_label = next_arrival_win.label
                    else:
                        # Si la fin est dans le passé ou très proche, utiliser la prochaine fenêtre
                        next_departure = next_window.end if next_window else None
                        next_departure_label = next_window.label if next_window else None
                        next_arrival = next_window.start if next_window else None
                        next_arrival_label = next_window.label if next_window else None
                        # Si on n'a pas de next_window, chercher la prochaine fenêtre future
                        if not next_departure:
                            next_departure = next(
                                (w.end for w in windows if w.end > now_local + timedelta(minutes=1)), None
                            )
                            if next_departure:
                                matching_window = next((w for w in windows if w.end == next_departure), None)
                                if matching_window:
                                    next_arrival = matching_window.start
                                    next_arrival_label = matching_window.label
                elif override_state is True and self._presence_override and self._presence_override.get("until"):
                    # Override avec une date de fin spécifiée
                    next_departure = self._presence_override["until"]
                    if next_departure > now_local + timedelta(minutes=1):
                        # Chercher la fenêtre qui commence après l'override
                        next_arrival_win = next((w for w in windows if w.start > next_departure), None)
                        if next_arrival_win:
                            next_arrival = next_arrival_win.start
                            next_arrival_label = next_arrival_win.label
                    else:
                        # Override dans le passé ou très proche, utiliser la prochaine fenêtre
                        next_departure = next_window.end if next_window else None
                        next_departure_label = next_window.label if next_window else None
                        next_arrival = next_window.start if next_window else None
                        next_arrival_label = next_window.label if next_window else None
                        # Si on n'a pas de next_window, chercher la prochaine fenêtre future
                        if not next_departure:
                            next_departure = next(
                                (w.end for w in windows if w.end > now_local + timedelta(minutes=1)), None
                            )
                            if next_departure:
                                matching_window = next((w for w in windows if w.end == next_departure), None)
                                if matching_window:
                                    next_arrival = matching_window.start
                                    next_arrival_label = matching_window.label
                else:
                    # Override sans date de fin ou cas spécial, utiliser la prochaine fenêtre
                    next_departure = next_window.end if next_window else None
                    next_departure_label = next_window.label if next_window else None
                    next_arrival = next_window.start if next_window else None
                    next_arrival_label = next_window.label if next_window else None
            else:
                # Quand l'enfant n'est pas présent, next_arrival est toujours la prochaine fenêtre de garde future
                # et next_departure est la fin de cette même prochaine fenêtre
                next_arrival = next_window.start if next_window else None
                next_arrival_label = next_window.label if next_window else None
                next_departure = next_window.end if next_window else None
                next_departure_label = next_window.label if next_window else None

                # S'assurer que next_departure est toujours dans le futur (avec marge d'1 minute)
                # Normalement next_window.end devrait toujours être dans le futur, mais sécurité supplémentaire
                if next_departure and next_departure <= now_local + timedelta(minutes=1):
                    # Si next_departure est dans le passé ou très proche, chercher la prochaine fenêtre après
                    next_departure_win = next((w for w in windows if w.end > now_local + timedelta(minutes=1)), None)
                    if next_departure_win:
                        next_departure = next_departure_win.end
                        next_departure_label = next_departure_win.label
                        next_arrival = next_departure_win.start
                        next_arrival_label = next_departure_win.label
                    else:
                        # Si aucune fenêtre future, next_arrival devrait aussi être None
                        next_arrival = None
                        next_arrival_label = None

            days_remaining = None
            target_dt = next_departure if is_present else next_arrival
            if target_dt:
                delta = target_dt - now_local
                days_remaining = max(0, round(delta.total_seconds() / 86400, 2))

            period, vacation_name = await self._determine_period(now_local)

        # Get next vacation information and raw holidays data
        (
            next_vacation_name,
            next_vacation_start,
            next_vacation_end,
            days_until_vacation,
            school_holidays_raw,
        ) = await self._get_next_vacation(now_local)

        attributes = {
            ATTR_LOCATION: self._config.get(CONF_LOCATION),
            ATTR_NOTES: self._config.get(CONF_NOTES),
            ATTR_ZONE: self._config.get(CONF_ZONE),
        }

        return CustodyComputation(
            is_present=is_present,
            next_arrival=next_arrival,
            next_arrival_label=next_arrival_label,
            next_departure=next_departure,
            next_departure_label=next_departure_label,
            days_remaining=days_remaining,
            current_period=period,
            vacation_name=vacation_name,
            next_vacation_name=next_vacation_name,
            next_vacation_start=next_vacation_start,
            next_vacation_end=next_vacation_end,
            days_until_vacation=days_until_vacation,
            school_holidays_raw=school_holidays_raw,
            windows=all_windows,
            attributes=attributes,
        )

    async def _build_windows(self, now: datetime) -> list[CustodyWindow]:
        """Generate presence windows from base pattern and vacation/custom rules.

        Two separate planning systems:
        1. Weekend/Pattern planning: Based on custody_type (even_weekends, alternate_week, etc.)
        2. Vacation planning: Based on vacation_rule (first_week_odd_year, first_half, etc.)

        Priority: Vacation rules > Custom rules > Normal pattern rules
        Vacation periods completely replace normal pattern windows during their entire duration.
        """
        # 1. Generate vacation windows first (needed to check overlaps for public holidays)
        # This creates custody windows during school holidays (e.g., first half, second half)
        # Also creates filter windows that cover the entire vacation period
        vacation_windows = await self._generate_vacation_windows(now)

        # Add parental day windows (Mother/Father days) to vacation windows for priority filtering
        parental_windows = self._build_parental_day_windows(now)
        vacation_windows.extend(parental_windows)

        # 2. Generate weekend/pattern windows based on custody_type
        # This creates the normal weekend schedule (e.g., even weekends, alternate weekends)
        # Pass vacation_windows to check if weekends/weeks fall during vacations before applying public holidays
        pattern_windows = self._generate_pattern_windows(now, vacation_windows)

        # 3. Load custom windows (manual overrides)
        custom_windows = self._load_custom_rules()

        # 4. Remove pattern windows that overlap with vacation periods
        # Vacation rules have priority: they completely replace normal rules during vacations
        # Filter windows ensure all weekends/weeks during vacations are removed
        filtered_pattern_windows = self._filter_windows_by_vacations(pattern_windows, vacation_windows)

        # 5. Separate display windows from filter windows
        # Filter windows are only used for filtering, not displayed in the final schedule
        vacation_display_windows = [w for w in vacation_windows if w.source != "vacation_filter"]

        # 6. Merge in priority order: vacation windows (highest), then custom, then filtered pattern
        merged = vacation_display_windows + custom_windows + filtered_pattern_windows
        # Filtrer les fenêtres qui se terminent dans le passé (avec marge de 365 jours pour l'historique)
        return [window for window in merged if window.end > now - timedelta(days=365)]

    def _build_parental_day_windows(self, now: datetime) -> list[CustodyWindow]:
        """Automatically create windows for Mother's day and Father's day."""
        if not self._config.get(CONF_AUTO_PARENT_DAYS, False):
            return []

        role = self._config.get(CONF_PARENTAL_ROLE, "none")
        if role == "none":
            return []

        windows = []
        # Calculate for current and next year to ensure upcoming ones are visible
        country = self._config.get(CONF_COUNTRY, "FR")
        for year in (now.year, now.year + 1):
            dates = get_parent_days(year, country)

            # Mother's Day
            m_day = dates.get("mother")
            if m_day:
                m_start = dt_util.as_local(datetime.combine(m_day, time(0, 0)))
                m_end = dt_util.as_local(datetime.combine(m_day, time(23, 59, 59)))

                if role == "mother":
                    windows.append(CustodyWindow(m_start, m_end, "Mother's Day", "special"))
                elif role == "father":
                    windows.append(CustodyWindow(m_start, m_end, "Mother's Day (Secondary parent)", "vacation_filter"))

            # Father's Day
            f_day = dates.get("father")
            if f_day:
                f_start = dt_util.as_local(datetime.combine(f_day, time(0, 0)))
                f_end = dt_util.as_local(datetime.combine(f_day, time(23, 59, 59)))

                if role == "father":
                    windows.append(CustodyWindow(f_start, f_end, "Father's Day", "special"))
                elif role == "mother":
                    windows.append(CustodyWindow(f_start, f_end, "Father's Day (Secondary parent)", "vacation_filter"))

        return windows

    def _build_recurring_windows(self, now: datetime) -> list[CustodyWindow]:
        """Generate recurring exception windows."""
        exceptions = self._config.get(CONF_EXCEPTIONS_RECURRING, [])
        if not isinstance(exceptions, list) or not exceptions:
            return []

        windows: list[CustodyWindow] = []
        horizon_end = now.date() + timedelta(days=365)
        range_start = now.date() - timedelta(days=365)

        for item in exceptions:
            try:
                weekday = int(item.get("weekday"))
            except (TypeError, ValueError):
                continue
            if weekday < 0 or weekday > 6:
                continue

            start_time = self._parse_time(item.get("start_time"))
            end_time = self._parse_time(item.get("end_time"))
            if not start_time or not end_time or end_time <= start_time:
                continue

            start_date = dt_util.parse_date(item.get("start_date")) if item.get("start_date") else None
            end_date = dt_util.parse_date(item.get("end_date")) if item.get("end_date") else None

            current = max(range_start, start_date) if start_date else range_start
            range_end = min(horizon_end, end_date) if end_date else horizon_end
            if current > range_end:
                continue

            days_ahead = (weekday - current.weekday()) % 7
            occ_date = current + timedelta(days=days_ahead)
            label = item.get("label") or "Recurring exception"

            while occ_date <= range_end:
                start_dt = datetime.combine(occ_date, start_time, tzinfo=self._tz)
                end_dt = datetime.combine(occ_date, end_time, tzinfo=self._tz)
                if end_dt > start_dt:
                    windows.append(
                        CustodyWindow(
                            start=start_dt,
                            end=end_dt,
                            label=label,
                            source="exception_recurring",
                        )
                    )
                occ_date += timedelta(days=7)

        return windows

    def _filter_windows_by_vacations(
        self, pattern_windows: list[CustodyWindow], vacation_windows: list[CustodyWindow]
    ) -> list[CustodyWindow]:
        """Remove or truncate pattern windows that overlap with vacation periods.

        Vacations (and special days like Mother's Day) have priority over normal pattern rules.
        Instead of removing the entire window on overlap, we subtract the overlapping part.
        """
        if not vacation_windows:
            return pattern_windows

        # Build a list of priority periods (start, end) for quick overlap checking.
        vacation_periods = [(vw.start, vw.end) for vw in vacation_windows if vw.source == "vacation_filter"]
        if not vacation_periods:
            # Fallback to display windows if no filter windows (should not happen for vacations)
            vacation_periods = [(vw.start, vw.end) for vw in vacation_windows]

        # Process each priority period one by one, subtracting from the set of pattern windows
        current_active_windows = list(pattern_windows)

        for vac_start, vac_end in vacation_periods:
            next_pass_windows = []
            for item in current_active_windows:
                # 1. No overlap at all? Keep the window as is.
                if item.start >= vac_end or item.end <= vac_start:
                    next_pass_windows.append(item)
                    continue

                # 2. Partials overlaps - Subtract the overlapping range
                # Handle the part before the vacation segment
                if item.start < vac_start:
                    next_pass_windows.append(CustodyWindow(item.start, vac_start, item.label, item.source))

                # Handle the part after the vacation segment
                if item.end > vac_end:
                    next_pass_windows.append(CustodyWindow(vac_end, item.end, item.label, item.source))

            current_active_windows = next_pass_windows

        return current_active_windows

    def _is_in_vacation_period(self, check_date: datetime, vacation_windows: list[CustodyWindow]) -> bool:
        """Check if a date falls within any vacation period.

        Args:
            check_date: Date to check
            vacation_windows: List of vacation windows (including filter windows)

        Returns:
            True if the date is within a vacation period, False otherwise
        """
        if not vacation_windows:
            return False

        for vac_window in vacation_windows:
            if vac_window.start <= check_date <= vac_window.end:
                return True
        return False

    def _generate_pattern_windows(
        self, now: datetime, vacation_windows: list[CustodyWindow] = None
    ) -> list[CustodyWindow]:
        """Create repeating windows from the selected custody type.

        Args:
            now: Current datetime
            vacation_windows: List of vacation windows to check for overlaps (public holidays not applied during vacations)
        """
        if vacation_windows is None:
            vacation_windows = []

        if not self._config.get(CONF_ENABLE_CUSTODY, True):
            return []

        custody_type = self._config.get(CONF_CUSTODY_TYPE, "alternate_week")
        type_def = CUSTODY_TYPES.get(custody_type) or CUSTODY_TYPES["alternate_week"]
        # Use a longer horizon (400 days) to support 365-day calendar sync
        horizon = now + timedelta(days=400)

        # Cas particulier : week-ends basés sur la parité ISO des semaines
        if custody_type == "alternate_weekend":
            windows: list[CustodyWindow] = []
            pointer = self._reference_start(now, custody_type)

            # Get public holidays for current and next year
            country = self._config.get(CONF_COUNTRY, "FR")
            alsace_moselle = self._config.get(CONF_ALSACE_MOSELLE, False)
            holidays = get_public_holidays(now.year, country, alsace_moselle) | get_public_holidays(
                now.year + 1, country, alsace_moselle
            )

            # Get reference_year to determine parity (even = even weeks, odd = odd weeks)
            reference_year = self._config.get(
                CONF_REFERENCE_YEAR_CUSTODY, self._config.get(CONF_REFERENCE_YEAR, "even")
            )
            target_parity = 0 if reference_year == "even" else 1  # 0 = even, 1 = odd

            # Ajuster le pointer pour commencer avant ou à la date actuelle
            # Si le pointer est trop loin dans le passé, avancer jusqu'à une semaine proche de maintenant
            # On avance de 2 semaines à la fois pour respecter l'alternance
            while pointer < now - timedelta(days=365):
                pointer += timedelta(days=14)  # Sauter 2 semaines (alternance)
                # Vérifier que le pointer a toujours la bonne parité
                if pointer.isocalendar()[1] % 2 != target_parity:
                    # Si on a perdu la parité, ajuster d'une semaine
                    pointer += timedelta(days=7)

            while pointer < horizon:
                iso_week = pointer.isocalendar().week
                week_parity = iso_week % 2  # 0 = even, 1 = odd
                if week_parity == target_parity:
                    # Determine weekend start day from config (Friday or Saturday)
                    weekend_start_day = self._config.get(CONF_WEEKEND_START_DAY, "friday")

                    # pointer is Monday of the week, so:
                    # pointer is Monday: +4=Fri, +5=Sat, +6=Sun, +7=Mon
                    if weekend_start_day == "saturday":
                        weekend_start = pointer + timedelta(days=5)  # Saturday
                    else:
                        weekend_start = pointer + timedelta(days=4)  # Friday (default)

                    # Resolve base end day
                    target_end_weekday = WEEKDAY_LOOKUP.get(self._end_day, 6)
                    days_to_end = (target_end_weekday - pointer.weekday()) % 7
                    base_end_date = pointer + timedelta(days=days_to_end)

                    # Check if end falls before start (weekend spanning)
                    if base_end_date < weekend_start:
                        base_end_date += timedelta(days=7)

                    # Default start/end
                    window_start = weekend_start
                    window_end = base_end_date
                    label_suffix = ""

                    # Resolve end date using helper
                    window_end = self._calculate_end_date(window_start, holidays)
                    label_suffix = (
                        " + Holiday"
                        if (window_end - window_start).days
                        > (target_end_weekday - pointer.weekday()) % 7
                        + (7 if (target_end_weekday - pointer.weekday()) % 7 == 0 else 0)
                        else ""
                    )
                    # Simplification of suffix logic for weekends
                    if window_end.date() != base_end_date.date():
                        label_suffix = " + Holiday"

                    # Get label from custody type definition
                    type_label = CUSTODY_TYPES.get(custody_type, {}).get("label", "Garde")
                    windows.append(
                        CustodyWindow(
                            start=self._apply_time(window_start, self._arrival_time),
                            end=self._apply_time(window_end, self._departure_time),
                            label=f"Garde - {type_label}{label_suffix}",
                            source="pattern",
                        )
                    )
                pointer += timedelta(days=7)
            return windows

        # Cas particulier : semaines alternées basées sur la parité ISO des semaines
        if custody_type == "alternate_week_parity":
            windows: list[CustodyWindow] = []
            pointer = self._reference_start(now, custody_type)

            # Get public holidays for current and next year
            country = self._config.get(CONF_COUNTRY, "FR")
            alsace_moselle = self._config.get(CONF_ALSACE_MOSELLE, False)
            holidays = get_public_holidays(now.year, country, alsace_moselle) | get_public_holidays(
                now.year + 1, country, alsace_moselle
            )

            # Get reference_year to determine parity (even = even weeks, odd = odd weeks)
            reference_year = self._config.get(
                CONF_REFERENCE_YEAR_CUSTODY, self._config.get(CONF_REFERENCE_YEAR, "even")
            )
            target_parity = 0 if reference_year == "even" else 1  # 0 = even, 1 = odd

            while pointer < now - timedelta(days=365):
                pointer += timedelta(days=14)
                if pointer.isocalendar()[1] % 2 != target_parity:
                    pointer += timedelta(days=7)

            while pointer < horizon:
                iso_week = pointer.isocalendar().week
                week_parity = iso_week % 2
                if week_parity == target_parity:
                    # Week starts Monday
                    monday = pointer

                    # Resolve end date using helper
                    target_end_weekday = WEEKDAY_LOOKUP.get(self._end_day, 6)
                    days_to_end = (target_end_weekday - monday.weekday()) % 7
                    if days_to_end == 0:
                        days_to_end = 7
                    base_end_date = monday + timedelta(days=days_to_end)

                    window_start = monday
                    window_end = self._calculate_end_date(window_start, holidays)

                    label_suffix = ""
                    # Extension check for label suffix
                    if window_end.date() > base_end_date.date():
                        label_suffix = " + Holiday"

                    # Get label from custody type definition
                    type_label = CUSTODY_TYPES.get(custody_type, {}).get("label", "Garde")
                    windows.append(
                        CustodyWindow(
                            start=self._apply_time(window_start, self._arrival_time),
                            end=self._apply_time(window_end, self._departure_time),
                            label=f"Garde - {type_label}{label_suffix}",
                            source="pattern",
                        )
                    )
                pointer += timedelta(days=7)
            return windows

        cycle_days = type_def["cycle_days"]
        pattern = type_def["pattern"]

        # Handle custom pattern if selected
        if custody_type == "custom" and self._config.get(CONF_CUSTOM_PATTERN):
            custom_states = str(self._config.get(CONF_CUSTOM_PATTERN)).split(",")
            cycle_days = len(custom_states)
            pattern = []
            if custom_states:
                current_state = custom_states[0]
                current_count = 0
                for state in custom_states:
                    if state == current_state:
                        current_count += 1
                    else:
                        pattern.append({"days": current_count, "state": current_state})
                        current_state = state
                        current_count = 1
                pattern.append({"days": current_count, "state": current_state})
        windows: list[CustodyWindow] = []
        reference_start = self._reference_start(now, custody_type)
        pointer = reference_start

        while pointer < horizon:
            offset = timedelta()
            for segment in pattern:
                segment_start = pointer + offset

                # Determine intended duration
                # For alternate_week, we use the end_day logic
                if custody_type == "alternate_week":
                    # Get public holidays
                    country = self._config.get(CONF_COUNTRY, "FR")
                    alsace_moselle = self._config.get(CONF_ALSACE_MOSELLE, False)
                    holidays = get_public_holidays(now.year, country, alsace_moselle) | get_public_holidays(
                        now.year + 1, country, alsace_moselle
                    )
                    segment_end = self._calculate_end_date(segment_start, holidays)
                    # For alternate_week, the next segment should start exactly when this one ends
                    actual_duration = segment_end - segment_start
                else:
                    # Cycled patterns: fixed duration + holiday extension
                    # Note: segment["days"] is total days.
                    # If 1 day: start Mon 08:00, end Mon 19:00 (duration 0 days in timedelta, but spans 1 day)
                    segment_end = segment_start + timedelta(days=segment["days"] - 1)

                    # Apply holiday extension
                    country = self._config.get(CONF_COUNTRY, "FR")
                    alsace_moselle = self._config.get(CONF_ALSACE_MOSELLE, False)
                    holidays = get_public_holidays(now.year, country, alsace_moselle) | get_public_holidays(
                        now.year + 1, country, alsace_moselle
                    )
                    segment_end = self._apply_holiday_extension(segment_end, holidays)

                    # For cycled patterns, we keep the original offset for the NEXT segment
                    # to avoid shifting the whole future schedule.
                    # Exception: if it's a "custom" pattern, we might want it to shift?
                    # No, usually patterns are fixed calendars.
                    actual_duration = timedelta(days=segment["days"])

                if segment["state"] == "on":
                    # Get label from custody type definition
                    type_label = CUSTODY_TYPES.get(custody_type, {}).get("label", "Garde")
                    windows.append(
                        CustodyWindow(
                            start=self._apply_time(segment_start, self._arrival_time),
                            end=self._apply_time(segment_end, self._departure_time),
                            label=f"Garde - {type_label}",
                            source="pattern",
                        )
                    )
                offset += actual_duration
            pointer += timedelta(days=cycle_days)

        return windows

    async def _generate_vacation_windows(self, now: datetime) -> list[CustodyWindow]:
        """Optional windows driven by vacation rules."""
        zone = self._config.get(CONF_ZONE)
        if not zone:
            return []
        country = self._config.get(CONF_COUNTRY, DEFAULT_COUNTRY)
        # Fetch holidays without year restriction to get current and next school years
        holidays = await self._holidays.async_list(country, zone)
        windows: list[CustodyWindow] = []
        # vacation_rule is now automatic based on year parity
        # For all holidays (including summer), use automatic parity logic:
        # odd year = first part, even year = second part (or vice versa)
        rule = None
        summer_mode = self._config.get(CONF_SUMMER_SPLIT_MODE, "half")

        for holiday in holidays:
            start, end, midpoint = self._effective_holiday_bounds(holiday)
            if end < now:
                continue

            # Always add a filter window covering the full effective vacation period.
            # This enforces: vacances scolaires > garde normale (no weekend/week pattern windows inside holidays).
            windows.append(
                CustodyWindow(
                    start=start,
                    end=end,
                    label=f"{holiday.name} - Full period (Filter)",
                    source="vacation_filter",
                )
            )

            # Automatic vacation rule based on year parity + split mode
            # Get reference_year to determine which parent gets vacations this year
            split_mode = self._config.get(CONF_VACATION_SPLIT_MODE, "odd_first")
            is_even_year = start.year % 2 == 0

            # Determine automatic rule:
            # - split_mode "odd_first": odd years -> first half, even years -> second half
            # - split_mode "odd_second": odd years -> second half, even years -> first half
            if split_mode == "odd_second":
                rule = "second_half" if not is_even_year else "first_half"
            else:
                rule = "first_half" if not is_even_year else "second_half"

            if not rule:
                continue

            # Handle summer quarter-split if enabled
            is_summer = any(kw in holiday.name.lower() for kw in ["été", "summer"]) or holiday.start.month in (7, 8)
            if is_summer and summer_mode == "quarter":
                # Split the whole summer duration [start, end] into 4 equal segments
                total_duration = end - start
                seg_duration = total_duration / 4

                parts = [
                    (start, start + seg_duration),
                    (start + seg_duration, start + 2 * seg_duration),
                    (start + 2 * seg_duration, start + 3 * seg_duration),
                    (start + 3 * seg_duration, end),
                ]

                # Parent with "first_half" rule gets parts 1 and 3
                # Parent with "second_half" rule gets parts 2 and 4
                if rule == "first_half":
                    target_parts = [parts[0], parts[2]]
                else:
                    target_parts = [parts[1], parts[3]]

                for p_start, p_end in target_parts:
                    if p_end > p_start:
                        windows.append(
                            CustodyWindow(
                                start=p_start,
                                end=p_end,
                                label=f"Vacances scolaires - {holiday.name} (Quinzaine)",
                                source="vacation",
                            )
                        )
                continue

            window_start = start
            window_end = end

            if rule == "first_week":
                # 1ère semaine : uniquement en années impaires
                if not is_even_year:
                    window_start = self._apply_time(start, self._arrival_time)
                    window_end = min(end, start + timedelta(days=7))
                    window_end = self._apply_time(window_end, self._departure_time)
                else:
                    # Année paire : pas de garde (car c'est la 2ème partie)
                    continue
            elif rule == "second_week":
                # 2ème semaine : uniquement en années paires
                if is_even_year:
                    window_start = start + timedelta(days=7)
                    window_start = self._apply_time(window_start, self._arrival_time)
                    window_end = min(end, window_start + timedelta(days=7))
                    window_end = self._apply_time(window_end, self._departure_time)
                else:
                    # Année impaire : pas de garde (car c'est la 1ère partie)
                    continue
            elif rule == "first_half":
                # 1ère moitié : attribuée selon le calcul de parité précédent
                window_start = start
                window_end = midpoint
            elif rule == "second_half":
                # 2ème moitié : attribuée selon le calcul de parité précédent
                window_start = midpoint
                window_end = end
            elif rule == "even_weeks":
                window_start = start
                if int(start.strftime("%U")) % 2 != 0:
                    window_start = start + timedelta(days=7)
                window_start = self._apply_time(window_start, self._arrival_time)
                window_end = min(end, window_start + timedelta(days=7))
                window_end = self._apply_time(window_end, self._departure_time)
            elif rule == "odd_weeks":
                window_start = start
                if int(start.strftime("%U")) % 2 == 0:
                    window_start = start + timedelta(days=7)
                window_start = self._apply_time(window_start, self._arrival_time)
                window_end = min(end, window_start + timedelta(days=7))
                window_end = self._apply_time(window_end, self._departure_time)
            elif rule == "even_weekends":
                days_until_saturday = (5 - start.weekday()) % 7
                saturday = start + timedelta(days=days_until_saturday)
                _, iso_week, _ = saturday.isocalendar()
                if iso_week % 2 != 0:
                    saturday += timedelta(days=7)
                sunday = saturday + timedelta(days=1)
                window_start = self._apply_time(saturday, self._arrival_time)
                window_end = min(end, self._apply_time(sunday, self._departure_time))
            elif rule == "odd_weekends":
                days_until_saturday = (5 - start.weekday()) % 7
                saturday = start + timedelta(days=days_until_saturday)
                _, iso_week, _ = saturday.isocalendar()
                if iso_week % 2 == 0:
                    saturday += timedelta(days=7)
                sunday = saturday + timedelta(days=1)
                window_start = self._apply_time(saturday, self._arrival_time)
                window_end = min(end, self._apply_time(sunday, self._departure_time))

            else:
                window_start = self._apply_time(start, self._arrival_time)
                window_end = self._apply_time(end, self._departure_time)

            if window_end <= window_start:
                continue

            translations = {
                "first_half": "1ère moitié",
                "second_half": "2ème moitié",
                "first_week": "1ère semaine",
                "second_week": "2ème semaine",
                "even_weeks": "semaines paires",
                "odd_weeks": "semaines impaires",
                "even_weekends": "week-ends pairs",
                "odd_weekends": "week-ends impairs",
            }
            rule_label = translations.get(rule, rule)

            windows.append(
                CustodyWindow(
                    start=window_start,
                    end=window_end,
                    label=f"Vacances scolaires - {holiday.name} ({rule_label})",
                    source="vacation",
                )
            )
        return windows

    def _load_custom_rules(self) -> list[CustodyWindow]:
        """Transform custom ISO ranges configured via options."""
        custom_rules = self._config.get(CONF_CUSTOM_RULES) or []
        windows: list[CustodyWindow] = []
        for rule in custom_rules:
            start = dt_util.parse_datetime(rule.get("start"))
            end = dt_util.parse_datetime(rule.get("end"))
            label = rule.get("label", "Custom rule")
            if not start or not end or end <= start:
                continue
            windows.append(
                CustodyWindow(
                    start=dt_util.as_local(start),
                    end=dt_util.as_local(end),
                    label=label,
                    source="custom",
                )
            )
        return windows

    def _reference_start(self, now: datetime, custody_type: str) -> datetime:
        """Return the datetime used as anchor for the cycle."""
        reference_year = now.year
        desired = self._config.get(CONF_REFERENCE_YEAR_CUSTODY, self._config.get(CONF_REFERENCE_YEAR, "even"))
        if desired == "even" and reference_year % 2 != 0:
            reference_year -= 1
        elif desired == "odd" and reference_year % 2 == 0:
            reference_year -= 1

        if custody_type in ("alternate_weekend", "alternate_week_parity"):
            # Use reference_year to determine parity (even = even weeks, odd = odd weeks)
            target_parity = 0 if desired == "even" else 1
            base = self._first_monday_with_week_parity(reference_year, target_parity)
            # For week-parity modes, always anchor on Monday; ignore start_day.
            return base
        else:
            base = datetime(reference_year, 1, 1, tzinfo=self._tz)

        start_day = WEEKDAY_LOOKUP.get(self._config.get(CONF_START_DAY, "monday").lower(), 0)
        delta = (start_day - base.weekday()) % 7
        return base + timedelta(days=delta)

    def _first_monday_with_week_parity(self, year: int, parity: int) -> datetime:
        """Return the first Monday of the ISO week with the requested parity (0 even / 1 odd)."""
        candidate = datetime(year, 1, 1, tzinfo=self._tz)
        # Go to next Monday
        candidate += timedelta(days=(7 - candidate.weekday()) % 7)
        while candidate.isocalendar().week % 2 != parity:
            candidate += timedelta(days=7)
        return candidate

    def _summer_week_parity_windows(
        self, start: datetime, end: datetime, target_parity: int, month: int
    ) -> list[CustodyWindow]:
        """Slice summer into week chunks based on even/odd parity."""
        windows: list[CustodyWindow] = []
        cursor = start
        while cursor < end:
            if cursor.month != month:
                cursor += timedelta(days=1)
                continue
            week_start = cursor - timedelta(days=cursor.weekday())
            week_end = min(end, week_start + timedelta(days=7))
            if week_start.isocalendar().week % 2 == target_parity:
                windows.append(
                    CustodyWindow(
                        start=week_start,
                        end=week_end,
                        label=(
                            f"Vacances scolaires - Semaine "
                            f"{'paire' if target_parity == 0 else 'impaire'} "
                            f"{week_start.isocalendar().week}"
                        ),
                        source="summer",
                    )
                )
            cursor = week_end
        return windows

    def _apply_time(self, dt_value: datetime, target: time) -> datetime:
        """Attach the configured time to a datetime."""
        return dt_value.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)

    def _effective_holiday_bounds(self, holiday) -> tuple[datetime, datetime, datetime]:
        """Return (effective_start, effective_end, midpoint) for a holiday.

        Custom vacation custody rules:
        - Effective start: previous Friday at arrival_time (e.g., school pickup Friday 16:15),
          even if the API indicates a Saturday start.
        - Effective end: previous Sunday at departure_time (e.g., Sunday 19:00),
          even if the API indicates a Monday reprise at 00:00.
        - Midpoint: exact half between effective start and effective end (midpoint time overrides standard times).
        """
        start_dt = dt_util.as_local(holiday.start)
        end_dt = dt_util.as_local(holiday.end)

        start_date = start_dt.date()
        end_date = end_dt.date()

        # If the API returns an end at 00:00, it's typically the "reprise" day (exclusive end)
        if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
            end_date = end_date - timedelta(days=1)

        # Effective start is the previous Friday (school pickup)
        effective_start_date = start_date
        while effective_start_date.weekday() != 4:  # Friday
            effective_start_date -= timedelta(days=1)

        # Effective end matches the configured end_day (usually Sunday or Monday)
        # We look for the next occurrence of end_day after the vacation end_date
        target_end_weekday = WEEKDAY_LOOKUP.get(self._end_day, 6)
        effective_end_date = end_date

        # If the holiday already ends on or after the target weekday,
        # we might need to go to the NEXT one to cover the weekend.
        # But if it ends on Monday 00:00 (FR), we want the previous Sunday.

        if end_dt.weekday() == 0 and end_dt.hour == 0:
            # Case France: Ends Monday 00:00 -> Effective end is the previous Sunday/Monday
            # We go back to the nearest target_end_weekday
            while effective_end_date.weekday() != target_end_weekday:
                effective_end_date -= timedelta(days=1)
        else:
            # Case BE/CH/LU: Ends Friday or Saturday -> Effective end is the following Sunday/Monday
            while effective_end_date.weekday() != target_end_weekday:
                effective_end_date += timedelta(days=1)

        effective_start = datetime.combine(effective_start_date, self._arrival_time, start_dt.tzinfo)
        effective_end = datetime.combine(effective_end_date, self._departure_time, end_dt.tzinfo)

        # Safety fallback: avoid inverted windows on unexpected API shapes
        if effective_end <= effective_start:
            effective_start = self._apply_time(start_dt, self._arrival_time)
            effective_end = self._apply_time(end_dt, self._departure_time)

        midpoint = effective_start + (effective_end - effective_start) / 2
        return effective_start, effective_end, midpoint

    def _parse_time(self, value: str) -> time:
        """Parse HH:MM strings into a time object."""
        try:
            hour, minute = value.split(":")
            return time(int(hour), int(minute))
        except (ValueError, AttributeError):
            return time(8, 0)

    async def _determine_period(self, now: datetime) -> tuple[str, str | None]:
        """Return ('school'|'vacation', holiday_name)."""
        zone = self._config.get(CONF_ZONE)
        if not zone:
            return "school", None

        country = self._config.get(CONF_COUNTRY, DEFAULT_COUNTRY)
        # Fetch holidays without year restriction to get current and next school years
        holidays = await self._holidays.async_list(country, zone)
        for holiday in holidays:
            effective_start, effective_end, _mid = self._effective_holiday_bounds(holiday)
            if effective_start <= now <= effective_end:
                return "vacation", holiday.name

        return "school", None

    async def _get_next_vacation(
        self, now: datetime
    ) -> tuple[str | None, datetime | None, datetime | None, int | None, list[dict[str, Any]]]:
        """Return information about the next upcoming vacation (custody-focused).

        Uses the *effective* vacation bounds (custom rules):
        - Start: previous Friday at arrival_time (pickup at school)
        - End: previous Sunday at departure_time (return Sunday evening)
        - Midpoint: exact half (time is preserved and overrides standard times)

        Returned start/end correspond to the next *custody segment* during that vacation
        (e.g., if rule is "second_half", start is the midpoint, not the vacation start).
        """
        zone = self._config.get(CONF_ZONE)
        if not zone:
            LOGGER.warning("No zone configured, cannot fetch school holidays")
            return None, None, None, None, []

        country = self._config.get(CONF_COUNTRY, DEFAULT_COUNTRY)
        # Fetch holidays without year restriction to get current and next school years
        LOGGER.debug("Fetching school holidays for country=%s, zone=%s", country, zone)
        holidays = await self._holidays.async_list(country, zone)
        LOGGER.debug("Retrieved %d holidays from API", len(holidays))

        if not holidays:
            LOGGER.warning("No holidays found for zone %s, year %s", zone, now.year)

        # Sort holidays by effective start date (more relevant than raw API start)
        sorted_holidays = sorted(holidays, key=lambda h: self._effective_holiday_bounds(h)[0])

        # Build raw holidays list for debugging/display
        # Filter to only show holidays from current calendar year onwards
        # This includes holidays from current school year and previous school year if they're in current year
        school_holidays_raw = []

        weekday_fr = {
            "Monday": "Lundi",
            "Tuesday": "Mardi",
            "Wednesday": "Mercredi",
            "Thursday": "Jeudi",
            "Friday": "Vendredi",
            "Saturday": "Samedi",
            "Sunday": "Dimanche",
        }

        for holiday in sorted_holidays:
            effective_start, effective_end, _midpoint = self._effective_holiday_bounds(holiday)

            # Only show upcoming/current holidays (based on effective end)
            if effective_end < now:
                continue
            school_holidays_raw.append(
                {
                    "name": holiday.name,
                    "official_start": dt_util.as_local(holiday.start).strftime("%d %B %Y"),
                    "official_end": dt_util.as_local(holiday.end).strftime("%d %B %Y"),
                    "official_start_weekday": weekday_fr.get(
                        dt_util.as_local(holiday.start).strftime("%A"),
                        dt_util.as_local(holiday.start).strftime("%A"),
                    ),
                    "official_end_weekday": weekday_fr.get(
                        dt_util.as_local(holiday.end).strftime("%A"),
                        dt_util.as_local(holiday.end).strftime("%A"),
                    ),
                    "effective_start": effective_start.strftime("%d %B %Y %H:%M"),
                    "effective_end": effective_end.strftime("%d %B %Y %H:%M"),
                }
            )

        # vacation_rule is now automatic based on reference_year + split mode
        split_mode = self._config.get(CONF_VACATION_SPLIT_MODE, "odd_first")
        summer_mode = self._config.get(CONF_SUMMER_SPLIT_MODE, "half")

        def _custody_segment_for_holiday(holiday_obj) -> tuple[datetime, datetime]:
            eff_start, eff_end, mid = self._effective_holiday_bounds(holiday_obj)

            # If custody management is disabled (Vacations Only), return the full vacation period
            if not self._config.get(CONF_ENABLE_CUSTODY, True):
                return eff_start, eff_end

            # Handle summer quarter-split if enabled
            is_summer = "été" in holiday_obj.name.lower() or holiday_obj.start.month in (7, 8)
            if is_summer and summer_mode == "quarter":
                total_duration = eff_end - eff_start
                seg_duration = total_duration / 4

                parts = [
                    (eff_start, eff_start + seg_duration),
                    (eff_start + seg_duration, eff_start + 2 * seg_duration),
                    (eff_start + 2 * seg_duration, eff_start + 3 * seg_duration),
                    (eff_start + 3 * seg_duration, eff_end),
                ]

                # Rule logic for parity
                is_even_year = eff_start.year % 2 == 0
                if split_mode == "odd_second":
                    rule_type = "second_half" if not is_even_year else "first_half"
                else:
                    rule_type = "first_half" if not is_even_year else "second_half"

                # Find the next segment for this user
                if rule_type == "first_half":
                    # User has parts 1 and 3. Return the one that is in the future.
                    if parts[0][1] > now:
                        return parts[0]
                    return parts[2]
                else:
                    # User has parts 2 and 4
                    if parts[1][1] > now:
                        return parts[1]
                    return parts[3]

            # Automatic vacation rule based on year parity + split mode
            is_even_year = eff_start.year % 2 == 0
            if split_mode == "odd_second":
                rule_for_year = "second_half" if not is_even_year else "first_half"
            else:
                rule_for_year = "first_half" if not is_even_year else "second_half"

            return (mid, eff_end) if rule_for_year == "second_half" else (eff_start, mid)

        # First, check if we're currently in a vacation (effective bounds)
        for holiday in sorted_holidays:
            eff_start, eff_end, _mid = self._effective_holiday_bounds(holiday)
            if eff_start <= now <= eff_end:
                seg_start, seg_end = _custody_segment_for_holiday(holiday)
                return (
                    holiday.name,
                    seg_start,
                    seg_end,
                    0,
                    school_holidays_raw,
                )

        # Not in vacation, find the next custody segment start
        next_vacation = None
        next_seg_start: datetime | None = None
        next_seg_end: datetime | None = None
        for holiday in sorted_holidays:
            seg_start, seg_end = _custody_segment_for_holiday(holiday)
            LOGGER.debug(
                "Checking holiday (custody segment): %s, seg_start=%s, seg_end=%s, now=%s",
                holiday.name,
                seg_start,
                seg_end,
                now,
            )
            if seg_start > now:
                next_vacation = holiday
                next_seg_start = seg_start
                next_seg_end = seg_end
                LOGGER.debug("Found next vacation custody segment: %s, start=%s", holiday.name, next_seg_start)
                break

        if not next_vacation:
            LOGGER.warning("No next vacation found after %s. Total holidays: %d", now, len(sorted_holidays))
            if sorted_holidays:
                LOGGER.debug("Last holiday: %s (ends %s)", sorted_holidays[-1].name, sorted_holidays[-1].end)
            return None, None, None, None, school_holidays_raw

        if next_seg_start is None or next_seg_end is None:
            return None, None, None, None, school_holidays_raw

        delta = next_seg_start - now
        days_until = max(0, round(delta.total_seconds() / 86400, 2))

        return (
            next_vacation.name,
            next_seg_start,
            next_seg_end,
            days_until,
            school_holidays_raw,
        )

    def _adjust_vacation_start(self, official_start: datetime, school_level: str) -> datetime:
        """Adjust vacation start date based on school level.

        - Primary: Friday afternoon (departure time)
          - L'API retourne le vendredi à 23h UTC, qui devient samedi 00h en heure locale
          - On extrait la date et on s'assure que c'est un vendredi (si c'est samedi, on recule d'1 jour)
        - Middle/High: Saturday at arrival time
          - Si l'API retourne samedi, on l'utilise directement
          - Sinon, on trouve le samedi suivant

        Args:
            official_start: Official vacation start date from API (en heure locale après conversion)
            school_level: "primary", "middle", or "high"

        Returns:
            Adjusted start datetime
        """

        if school_level == "primary":
            # Primary: Friday afternoon at departure time
            # L'API retourne le vendredi à 23h UTC, qui devient samedi 00h en heure locale
            # On extrait la date et on s'assure que c'est un vendredi
            date_only = official_start.date()
            weekday = date_only.weekday()  # 0=Monday, 4=Friday, 5=Saturday
            weekday_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

            LOGGER.debug(
                "Adjusting vacation start for primary: official_start=%s (%s), weekday=%d",
                official_start,
                weekday_names[weekday],
                weekday,
            )

            # Si c'est samedi (5), c'est que l'API a retourné vendredi 23h UTC qui est devenu samedi 00h local
            # On recule d'1 jour pour avoir le vendredi
            if weekday == 5:  # Saturday
                date_only = date_only - timedelta(days=1)
                LOGGER.debug("Was Saturday, adjusted to Friday: %s", date_only)
            # Si c'est déjà vendredi (4), on l'utilise directement

            # Créer un nouveau datetime avec la date corrigée et l'heure d'arrivée (vendredi sortie d'école)
            # Pour les vacances, on utilise l'heure d'arrivée car c'est le moment où l'enfant arrive
            friday_datetime = datetime.combine(date_only, self._arrival_time, official_start.tzinfo)
            LOGGER.debug("Final adjusted datetime: %s", friday_datetime)
            return friday_datetime
        else:
            # Middle/High: Saturday at arrival time
            # If official_start is Saturday, use it; otherwise find the next Saturday
            if official_start.weekday() == 5:  # Saturday
                saturday = official_start
            else:
                # Find the next Saturday
                days_to_saturday = (5 - official_start.weekday()) % 7
                if days_to_saturday == 0:
                    days_to_saturday = 7
                saturday = official_start + timedelta(days=days_to_saturday)
            return self._apply_time(saturday, self._arrival_time)

    def _force_vacation_end(self, official_end: datetime) -> datetime:
        """Force the vacation end to Sunday 19:00 if it falls on a Monday (school resume)."""
        # API end is usually Monday 00:00 (which is Sunday night)
        # If it's Monday 00:00, move to Sunday departure_time
        if official_end.weekday() == 0 and official_end.hour == 0 and official_end.minute == 0:
            sunday = official_end - timedelta(days=1)
            return self._apply_time(sunday, self._departure_time)

        # Also handle cases where it might be Monday at some other time or Sunday at 00:00
        # The key is: if the vacation ends at the start of a Monday, custody ends Sunday evening
        if official_end.weekday() == 0:  # Monday
            sunday = official_end - timedelta(days=official_end.weekday() + 1 if official_end.weekday() < 6 else 0)
            # Actually, just get the Sunday before this Monday
            sunday = official_end - timedelta(days=1)
            return self._apply_time(sunday, self._departure_time)

        return self._apply_time(official_end, self._departure_time)

    def _evaluate_override(self, now: datetime) -> bool | None:
        """Return override state if active."""
        if not self._presence_override:
            return None
        until: datetime | None = self._presence_override["until"]
        if until and now > dt_util.as_local(until):
            self._presence_override = None
            return None
        return self._presence_override["state"] == "on"

    def _build_virtual_window(self, now: datetime) -> CustodyWindow:
        """Fallback window when override requests presence without schedule."""
        return CustodyWindow(start=now, end=now + timedelta(hours=1), label="Override", source="override")
