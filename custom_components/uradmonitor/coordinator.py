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
from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_DEVICE_ID,
)

_LOGGER = logging.getLogger(__name__)


def merge_device_data(
    device_id: str,
    *,
    local_data: Mapping[str, Any] | None = None,
    cloud_data: Mapping[str, Any] | None = None,
    local_available: bool = True,
    cloud_available: bool = True,
) -> dict[str, Any]:
    """Merge cloud data with local data, giving local values precedence."""
    merged: dict[str, Any] = {}
    if cloud_available and cloud_data:
        cloud_values = cloud_data.get(device_id, cloud_data)
        if isinstance(cloud_values, Mapping):
            merged.update(cloud_values)
    if local_available and local_data:
        local_values = dict(local_data)
        if local_values.get("ch2o") is not None:
            local_values["ch2o"] = float(local_values["ch2o"]) * 1000
        merged.update(local_values)
    return merged


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
            local_source = self.entry.data.get("sources", {}).get(ACCESS_MODE_LOCAL, {})
            response = await self.client.async_get_local_data(
                local_source.get("host", self.entry.data.get("host")),
                local_source.get("port", self.entry.data.get("port", 80)),
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
    return entry.data.get(CONF_ACCESS_MODE) == ACCESS_MODE_CLOUD or (
        ACCESS_MODE_CLOUD in entry.data.get("sources", {})
    )


def has_local_source(entry: ConfigEntry) -> bool:
    """Return whether an entry has a local API source."""
    return entry.data.get(CONF_ACCESS_MODE) != ACCESS_MODE_CLOUD and (
        entry.data.get(CONF_ACCESS_MODE) == ACCESS_MODE_LOCAL
        or ACCESS_MODE_LOCAL in entry.data.get("sources", {})
    )


class UradmonitorCombinedCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Combine readings from local and cloud coordinators for one device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        local: UradmonitorCoordinator | None,
        cloud: UradmonitorCoordinator | None,
    ) -> None:
        """Initialize the combined coordinator."""
        self.local = local
        self.cloud = cloud
        self.units_normalized = True
        self.device_id = str(entry.data[CONF_DEVICE_ID])
        self._remove_listeners: list[Any] = []
        super().__init__(
            hass,
            _LOGGER,
            name=f"uRADMonitor {self.device_id}",
            config_entry=entry,
            update_interval=None,
            always_update=False,
        )
        for source in (local, cloud):
            if source is not None:
                self._remove_listeners.append(
                    source.async_add_listener(self._source_updated)
                )
        self._update_merged_data()

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the latest merged source data."""
        self._update_merged_data()
        return self.data or {}

    def _source_updated(self) -> None:
        """Merge data whenever either source coordinator updates."""
        self._update_merged_data()

    def _update_merged_data(self) -> None:
        """Merge available local data over cloud data."""
        local_available = self.local is not None and self.local.last_update_success
        cloud_available = self.cloud is not None and self.cloud.last_update_success
        merged = merge_device_data(
            self.device_id,
            local_data=self.local.data if local_available and self.local else None,
            cloud_data=self.cloud.data if cloud_available and self.cloud else None,
            local_available=local_available,
            cloud_available=cloud_available,
        )
        if merged:
            self.async_set_updated_data(merged)
        elif local_available or cloud_available:
            self.async_set_updated_data({})
        else:
            self.async_set_update_error(
                UpdateFailed("All UradMonitor sources are unavailable")
            )

    def device_data(self, device_id: str) -> dict[str, Any]:
        """Return merged data for the configured device."""
        return self.data if self.data and device_id == self.device_id else {}

    async def async_shutdown(self) -> None:
        """Remove source listeners before shutting down."""
        for remove_listener in self._remove_listeners:
            remove_listener()
        self._remove_listeners.clear()
        await super().async_shutdown()
