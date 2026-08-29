"""Config flow for uradmonitor."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_API_KEY,
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
)


class UradmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a uradmonitor config flow."""

    VERSION = 1

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
        if user_input is not None:
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
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure a device using the cloud API."""
        if user_input is not None:
            return self.async_create_entry(
                title="uradmonitor cloud",
                data={**user_input, CONF_ACCESS_MODE: ACCESS_MODE_CLOUD},
            )

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema({vol.Required(CONF_CLOUD_API_KEY): str}),
        )
