"""Data coordinators for local and cloud uRADMonitor data."""

import asyncio
import logging
from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api.client import UradmonitorApiClient, UradmonitorApiError
from .const import ACCESS_MODE_CLOUD, CONF_ACCESS_MODE, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


class UradmonitorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate local data or a shared cloud device list."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: UradmonitorApiClient,
        update_interval: int,
        *,
        cloud: bool,
    ) -> None:
        """Initialize a coordinator."""
        self.client = client
        self.cloud = cloud
        self.entry = entry
        self._initial_local_refresh = not cloud
        super().__init__(
            hass,
            _LOGGER,
            name=f"uRADMonitor {'cloud' if cloud else entry.data.get(CONF_DEVICE_ID)}",
            config_entry=entry,
            update_interval=timedelta(seconds=update_interval),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize one polling response."""
        _LOGGER.debug("Updating UradMonitor %s coordinator", self.name)
        try:
            if self.cloud:
                devices = await self.client.async_get_devices()
                return {
                    str(device["id"]): {
                        key[5:]: value
                        for key, value in device.items()
                        if key.startswith("last_") and value is not None
                    }
                    for device in devices
                    if device.get("id")
                }

            # The embedded status page is used only during configuration to
            # obtain metadata.  Runtime readings must come from /j because
            # the HTML differs between hardware variants.
            if self._initial_local_refresh:
                await asyncio.sleep(2)
            response = await self.client.async_get_local_data(
                self.entry.data["host"],
                self.entry.data.get("port", 80),
            )
            data = response.get("data", response)
            if not isinstance(data, Mapping):
                raise UpdateFailed("Local device returned an unexpected data object")
            self._initial_local_refresh = False
            return dict(data)
        except UradmonitorApiError as err:
            raise UpdateFailed(str(err)) from err

    def device_data(self, device_id: str) -> dict[str, Any]:
        """Return normalized data for one device."""
        if self.cloud:
            return self.data.get(device_id, {})
        return self.data

    def set_update_interval(self, seconds: int) -> None:
        """Change the polling interval and reschedule future refreshes."""
        self.update_interval = timedelta(seconds=seconds)
        self._schedule_refresh()


def is_cloud_entry(entry: ConfigEntry) -> bool:
    """Return whether an entry uses the cloud API."""
    return entry.data.get(CONF_ACCESS_MODE) == ACCESS_MODE_CLOUD
