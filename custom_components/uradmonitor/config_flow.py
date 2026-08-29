"""Config flow for uradmonitor."""

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
from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
)


class UradmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a uradmonitor config flow."""

    VERSION = 1

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
                local_data = await client.async_get_local_data(
                    user_input[CONF_HOST], user_input.get(CONF_PORT, 80)
                )
            except UradmonitorApiError:
                errors["base"] = "cannot_connect"
            else:
                if device_id := local_data.get("id"):
                    await self.async_set_unique_id(str(device_id))
                    self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data={**user_input, CONF_ACCESS_MODE: ACCESS_MODE_LOCAL},
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
                title=self._device_label(device),
                data={
                    CONF_ACCESS_MODE: ACCESS_MODE_CLOUD,
                    CONF_CLOUD_USER_ID: self._cloud_client.user_id,
                    CONF_CLOUD_USER_KEY: self._cloud_client.user_key,
                    CONF_DEVICE_ID: device_id,
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
