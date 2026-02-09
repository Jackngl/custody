"""Sensor platform for Custody Schedule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from . import CustodyScheduleCoordinator
from .const import (
    ATTR_CURRENT_PERIOD,
    ATTR_CUSTODY_TYPE,
    ATTR_DAYS_REMAINING,
    ATTR_DAYS_UNTIL_VACATION,
    ATTR_NEXT_ARRIVAL,
    ATTR_NEXT_DEPARTURE,
    ATTR_NEXT_VACATION_END,
    ATTR_NEXT_VACATION_NAME,
    ATTR_NEXT_VACATION_START,
    ATTR_SCHOOL_HOLIDAYS_RAW,
    ATTR_VACATION_NAME,
    CONF_CHILD_NAME,
    CONF_CHILD_NAME_DISPLAY,
    CONF_PHOTO,
    DOMAIN,
)
from .schedule import CustodyComputation


@dataclass(slots=True)
class SensorDefinition:
    """Meta description for each logical sensor."""

    key: str
    icon: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    unit: str | None = None


SENSORS: tuple[SensorDefinition, ...] = (
    SensorDefinition("next_arrival", "mdi:calendar-clock", SensorDeviceClass.TIMESTAMP),
    SensorDefinition("next_departure", "mdi:calendar-arrow-right", SensorDeviceClass.TIMESTAMP),
    SensorDefinition(
        "days_remaining",
        "mdi:clock-end",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        UnitOfTime.DAYS,
    ),
    SensorDefinition("current_period", "mdi:school"),
    SensorDefinition("next_vacation_name", "mdi:calendar-star"),
    SensorDefinition("next_vacation_start", "mdi:calendar-start", SensorDeviceClass.TIMESTAMP),
    SensorDefinition(
        "days_until_vacation",
        "mdi:calendar-clock",
        SensorDeviceClass.DURATION,
        SensorStateClass.MEASUREMENT,
        UnitOfTime.DAYS,
    ),
    SensorDefinition("next_change", "mdi:calendar-sync"),
    SensorDefinition("parent_in_charge", "mdi:account-child-circle"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Custody Schedule sensors."""
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        from .const import LOGGER

        LOGGER.error("Custody schedule entry %s not found in hass.data", entry.entry_id)
        return

    coordinator: CustodyScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    child_name_display = entry.data.get(CONF_CHILD_NAME_DISPLAY, entry.data.get(CONF_CHILD_NAME))
    child_name_normalized = entry.data.get(CONF_CHILD_NAME, entry.data.get(CONF_CHILD_NAME_DISPLAY))

    entities = [
        CustodyScheduleSensor(coordinator, entry, definition, child_name_display, child_name_normalized)
        for definition in SENSORS
    ]
    async_add_entities(entities)


class CustodyScheduleSensor(CoordinatorEntity[CustodyComputation], SensorEntity):
    """Represent a derived sensor from the custody schedule state."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CustodyScheduleCoordinator,
        entry: ConfigEntry,
        definition: SensorDefinition,
        child_name_display: str,
        child_name_normalized: str,
    ) -> None:
        super().__init__(coordinator)
        self._definition = definition
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
        self._attr_translation_key = definition.key
        self._attr_icon = definition.icon
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=child_name_display,
            manufacturer="Custody",
            model="Custody Planning",
            sw_version="1.8.31",
        )
        self.entity_id = f"sensor.{slugify(child_name_normalized)}_{definition.key}"
        photo = entry.data.get(CONF_PHOTO)
        if photo:
            self._attr_entity_picture = photo

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        data = self.coordinator.data
        if not data:
            return None

        key = self._definition.key
        if key == "next_arrival":
            return dt_util.as_local(data.next_arrival) if data.next_arrival else None
        if key == "next_departure":
            return dt_util.as_local(data.next_departure) if data.next_departure else None
        if key == "days_remaining":
            return data.days_remaining
        if key == "current_period":
            if data.current_period == "vacation" and data.vacation_name:
                return data.vacation_name
            return data.current_period
        if key == "next_vacation_name":
            return data.next_vacation_name
        if key == "next_vacation_start":
            return dt_util.as_local(data.next_vacation_start) if data.next_vacation_start else None
        if key == "days_until_vacation":
            return data.days_until_vacation
        if key == "next_change":
            if not data.next_arrival and not data.next_departure:
                return None
            target = data.next_departure if data.is_present else data.next_arrival
            label = data.next_departure_label if data.is_present else data.next_arrival_label
            if not target:
                return None

            # Use relative formatting for "soon" events, or absolute for distant ones
            diff = target - dt_util.now()
            if diff < timedelta(days=1):
                time_str = target.strftime("%H:%M")
            else:
                # Localized day name
                weekday = target.weekday()  # 0 = Monday, 6 = Sunday
                lang = getattr(self.hass.config, "language", "en")
                if lang.startswith("fr"):
                    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                    day_name = days[weekday]
                else:
                    day_name = target.strftime("%A")
                time_str = f"{day_name} {target.strftime('%d/%m')}"

            if label:
                # Clean up label if it's too long or repetitive
                clean_label = label.replace("Garde - ", "").replace("Vacances scolaires - ", "")
                return f"{time_str} ({clean_label})"
            return time_str

        if key == "parent_in_charge":
            return "home" if data.is_present else "away"

        return None

    @property
    def icon(self) -> str | None:
        """Return dynamic icon."""
        data = self.coordinator.data
        if not data:
            return self._attr_icon

        key = self._definition.key
        if key == "current_period":
            if data.current_period == "vacation":
                return "mdi:beach"
            return "mdi:home-clock"

        if key == "days_remaining":
            return "mdi:timer-sand"

        if key == "parent_in_charge":
            return "mdi:home-account" if data.is_present else "mdi:account-arrow-right"

        return self._attr_icon

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional metadata shared across sensors."""
        data = self.coordinator.data
        if not data:
            return {}

        attrs: dict[str, Any] = {
            ATTR_CUSTODY_TYPE: self._entry.data.get("custody_type"),
            ATTR_CURRENT_PERIOD: data.current_period,
            ATTR_VACATION_NAME: data.vacation_name,
            ATTR_NEXT_ARRIVAL: dt_util.as_local(data.next_arrival) if data.next_arrival else None,
            "next_arrival_label": data.next_arrival_label,
            ATTR_NEXT_DEPARTURE: dt_util.as_local(data.next_departure) if data.next_departure else None,
            "next_departure_label": data.next_departure_label,
            ATTR_DAYS_REMAINING: data.days_remaining,
            ATTR_NEXT_VACATION_NAME: data.next_vacation_name,
            ATTR_NEXT_VACATION_START: dt_util.as_local(data.next_vacation_start) if data.next_vacation_start else None,
            ATTR_NEXT_VACATION_END: dt_util.as_local(data.next_vacation_end) if data.next_vacation_end else None,
            ATTR_DAYS_UNTIL_VACATION: data.days_until_vacation,
            ATTR_SCHOOL_HOLIDAYS_RAW: data.school_holidays_raw,
        }
        attrs.update(data.attributes)
        return {key: value for key, value in attrs.items() if value is not None}
