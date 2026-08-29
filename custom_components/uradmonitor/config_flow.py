"""Config flow for uradmonitor."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_API_TOKEN,
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_USERNAME,
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
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_HOST, "uradmonitor"),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_MODE, default=ACCESS_MODE_LOCAL): vol.In(
                    [ACCESS_MODE_LOCAL, ACCESS_MODE_CLOUD]
                ),
                vol.Optional(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=80): vol.Coerce(int),
                vol.Optional(CONF_API_TOKEN): str,
                vol.Optional(CONF_CLOUD_USERNAME): str,
                vol.Optional(CONF_CLOUD_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
