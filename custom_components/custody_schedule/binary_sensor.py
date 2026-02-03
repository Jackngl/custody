"""Binary sensor for current presence."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import CustodyScheduleCoordinator
from .const import (
    ATTR_CUSTODY_TYPE,
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the binary sensor."""
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        from .const import LOGGER

        LOGGER.error("Custody schedule entry %s not found in hass.data", entry.entry_id)
        return

    coordinator: CustodyScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    child_name = entry.data.get(CONF_CHILD_NAME_DISPLAY, entry.data.get(CONF_CHILD_NAME))
    async_add_entities([CustodyPresenceBinarySensor(coordinator, entry, child_name)])


class CustodyPresenceBinarySensor(CoordinatorEntity[CustodyComputation], BinarySensorEntity):
    """Représente le statut de présence de l'enfant (garde classique ou vacances scolaires)."""

    _attr_device_class = BinarySensorDeviceClass.PRESENCE
    _attr_has_entity_name = True
    _attr_translation_key = "presence"

    def __init__(self, coordinator: CustodyScheduleCoordinator, entry: ConfigEntry, child_name: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_presence"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=child_name,
            manufacturer="Custody",
            model="Custody Planning",
            sw_version=entry.version if hasattr(entry, "version") else "1.8.7",
        )
        self.entity_id = f"binary_sensor.{slugify(child_name)}_presence"
        photo = entry.data.get(CONF_PHOTO)
        if photo:
            self._attr_entity_picture = photo

    @property
    def is_on(self) -> bool | None:
        """Return presence state."""
        data = self.coordinator.data
        return data.is_present if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose additional metadata for automations."""
        data = self.coordinator.data
        if not data:
            return {}

        return {
            "child_name": self._entry.data.get(CONF_CHILD_NAME_DISPLAY, self._entry.data.get(CONF_CHILD_NAME)),
            ATTR_CUSTODY_TYPE: self._entry.data.get("custody_type"),
            ATTR_NEXT_ARRIVAL: data.next_arrival.isoformat() if data.next_arrival else None,
            ATTR_NEXT_DEPARTURE: data.next_departure.isoformat() if data.next_departure else None,
            ATTR_VACATION_NAME: data.vacation_name,
            ATTR_NEXT_VACATION_NAME: data.next_vacation_name,
            ATTR_NEXT_VACATION_START: data.next_vacation_start.isoformat() if data.next_vacation_start else None,
            ATTR_NEXT_VACATION_END: data.next_vacation_end.isoformat() if data.next_vacation_end else None,
            ATTR_DAYS_UNTIL_VACATION: data.days_until_vacation,
            ATTR_SCHOOL_HOLIDAYS_RAW: data.school_holidays_raw,
        }
