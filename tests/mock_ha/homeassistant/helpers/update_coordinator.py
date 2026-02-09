from typing import Generic, TypeVar

_T = TypeVar("_T")


class DataUpdateCoordinator(Generic[_T]):
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval

    async def async_config_entry_first_refresh(self):
        pass


class UpdateFailed(Exception):
    pass
