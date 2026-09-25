"""Cloud-device setup flow."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api.client import UradmonitorApiClient, UradmonitorApiError
from .config_flow_common import add_source_to_existing, configured_entry
from .const import (
    ACCESS_MODE_CLOUD,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DETECTOR,
    CONF_DEVICE_ID,
    CONF_DEVICE_TYPE,
    CONF_HARDWARE_VERSION,
    CONF_SOFTWARE_VERSION,
    CONF_SOURCES,
)

_LOGGER = logging.getLogger(__name__)


class CloudConfigFlowMixin:
    """Provide cloud transport setup to the main config flow."""

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Authenticate with the cloud API and select one device."""
        errors: dict[str, str] = {}
        if user_input is not None and self._cloud_client is None:
            self._cloud_client = UradmonitorApiClient(
                async_get_clientsession(self.hass),
                user_id=user_input[CONF_CLOUD_USER_ID],
                user_key=user_input[CONF_CLOUD_USER_KEY],
            )
            try:
                self._cloud_devices = await self._cloud_client.async_get_devices()
            except UradmonitorApiError:
                _LOGGER.error(
                    "Unable to retrieve devices from the UradMonitor cloud API"
                )
                self._cloud_client = None
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_cloud_device()

        if self._cloud_client is not None:
            return await self.async_step_cloud_device(user_input)
        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLOUD_USER_ID): str,
                    vol.Required(CONF_CLOUD_USER_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_cloud_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select one device returned by the cloud API."""
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = next(
                device for device in self._cloud_devices
                if str(device.get("id")) == device_id
            )
            assert self._cloud_client is not None
            await self.async_set_unique_id(str(device_id))
            source = {
                CONF_CLOUD_USER_ID: self._cloud_client.user_id,
                CONF_CLOUD_USER_KEY: self._cloud_client.user_key,
            }
            metadata = self._cloud_metadata(device)
            existing = configured_entry(self, str(device_id))
            if existing is not None:
                return add_source_to_existing(
                    self, existing, ACCESS_MODE_CLOUD, source, metadata
                )
            return self.async_create_entry(
                title=self._device_name(str(device_id)),
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_SOURCES: {ACCESS_MODE_CLOUD: source},
                    **metadata,
                },
            )

        options = [
            SelectOptionDict(value=str(device["id"]), label=self._device_label(device))
            for device in self._cloud_devices
            if device.get("id")
        ]
        if not options:
            return self.async_abort(reason="no_devices")
        return self.async_show_form(
            step_id="cloud_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
        )

    @staticmethod
    def _device_label(device: dict[str, Any]) -> str:
        """Return a useful label for a cloud device."""
        device_id = str(device["id"])
        name = device.get("note") or device.get("city") or "UradMonitor"
        return f"{name} (ID: {device_id})"

    @staticmethod
    def _device_name(device_id: str) -> str:
        """Return the default Home Assistant device name."""
        return device_id

    @staticmethod
    def _cloud_metadata(device: dict[str, Any]) -> dict[str, str]:
        """Extract shared metadata from a cloud device response."""
        metadata = {
            CONF_DEVICE_TYPE: device.get("type"),
            CONF_DETECTOR: device.get("detector"),
            CONF_HARDWARE_VERSION: device.get("versionhw"),
            CONF_SOFTWARE_VERSION: device.get("versionsw"),
        }
        return {key: str(value) for key, value in metadata.items() if value is not None}
