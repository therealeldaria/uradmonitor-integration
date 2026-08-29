"""Config flow for uradmonitor."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api.client import UradmonitorApiClient, UradmonitorApiError
from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DETECTOR,
    CONF_DEVICE_ID,
    CONF_DEVICE_TYPE,
    CONF_HARDWARE_VERSION,
    CONF_HOST,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_SOFTWARE_VERSION,
    DEFAULT_CLOUD_POLL_INTERVAL,
    DEFAULT_LOCAL_POLL_INTERVAL,
    DOMAIN,
    POLL_INTERVAL_OPTIONS,
)
from .coordinator import is_cloud_entry

_LOGGER = logging.getLogger(__name__)


class UradmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a uradmonitor config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        _config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for polling settings."""
        return UradmonitorOptionsFlow()

    def __init__(self) -> None:
        """Initialize a config flow."""
        self._cloud_client: UradmonitorApiClient | None = None
        self._cloud_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup form."""
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_MODE, default=ACCESS_MODE_LOCAL): vol.In(
                    [ACCESS_MODE_LOCAL, ACCESS_MODE_CLOUD]
                ),
            }
        )
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        if user_input[CONF_ACCESS_MODE] == ACCESS_MODE_LOCAL:
            return await self.async_step_local()
        return await self.async_step_cloud()

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure a device using its local API."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = UradmonitorApiClient(async_get_clientsession(self.hass))
            try:
                metadata = await client.async_get_local_metadata(
                    user_input[CONF_HOST], user_input.get(CONF_PORT, 80)
                )
            except UradmonitorApiError:
                _LOGGER.warning(
                    "Unable to retrieve optional metadata from local "
                    "UradMonitor at %s:%s",
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, 80),
                    exc_info=True,
                )
                metadata = {}

            device_id = metadata.get(CONF_DEVICE_ID)
            if not device_id:
                try:
                    local_data = await client.async_get_local_data(
                        user_input[CONF_HOST], user_input.get(CONF_PORT, 80)
                    )
                except UradmonitorApiError:
                    _LOGGER.error(
                        "Unable to validate local UradMonitor at %s:%s",
                        user_input[CONF_HOST],
                        user_input.get(CONF_PORT, 80),
                        exc_info=True,
                    )
                    errors["base"] = "cannot_connect"
                else:
                    device_id = self._local_device_id(local_data)

            if not device_id:
                _LOGGER.error("Local UradMonitor response did not contain a device ID")
                errors["base"] = "invalid_response"
            else:
                device_id = str(device_id)
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=self._device_name(device_id),
                    data={
                        **user_input,
                        CONF_ACCESS_MODE: ACCESS_MODE_LOCAL,
                        CONF_DEVICE_ID: device_id,
                        **metadata,
                    },
                )

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=80): vol.Coerce(int),
                }
            ),
            errors=errors,
        )

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
                    "Unable to retrieve devices from the UradMonitor cloud API",
                    exc_info=True,
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
                device
                for device in self._cloud_devices
                if str(device.get("id")) == device_id
            )
            assert self._cloud_client is not None
            await self.async_set_unique_id(str(device_id))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._device_name(str(device_id)),
                data={
                    CONF_ACCESS_MODE: ACCESS_MODE_CLOUD,
                    CONF_CLOUD_USER_ID: self._cloud_client.user_id,
                    CONF_CLOUD_USER_KEY: self._cloud_client.user_key,
                    CONF_DEVICE_ID: device_id,
                    **self._cloud_metadata(device),
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

    @staticmethod
    def _local_device_id(data: dict[str, Any]) -> str | None:
        """Extract the device ID from a local JSON response."""
        device_id = data.get("id")
        if device_id is None and isinstance(data.get("data"), dict):
            device_id = data["data"].get("id")
        return str(device_id) if device_id is not None else None


class UradmonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle polling interval changes."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage polling interval options."""
        config_entry = self.config_entry
        default = (
            DEFAULT_CLOUD_POLL_INTERVAL
            if is_cloud_entry(config_entry)
            else DEFAULT_LOCAL_POLL_INTERVAL
        )
        if user_input is not None:
            options = {CONF_POLL_INTERVAL: int(user_input[CONF_POLL_INTERVAL])}
            if is_cloud_entry(config_entry):
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        entry.entry_id != config_entry.entry_id
                        and is_cloud_entry(entry)
                        and entry.data.get(CONF_CLOUD_USER_ID)
                        == config_entry.data.get(CONF_CLOUD_USER_ID)
                        and entry.data.get(CONF_CLOUD_USER_KEY)
                        == config_entry.data.get(CONF_CLOUD_USER_KEY)
                    ):
                        self.hass.config_entries.async_update_entry(
                            entry, options=options
                        )
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=str(
                            config_entry.options.get(CONF_POLL_INTERVAL, default)
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=str(seconds),
                                    label=f"{seconds // 60} minutes",
                                )
                                for seconds in POLL_INTERVAL_OPTIONS
                            ]
                        )
                    ),
                }
            ),
        )
