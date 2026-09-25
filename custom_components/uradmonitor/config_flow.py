"""Top-level uRADMonitor configuration flow."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry

from .const import ACCESS_MODE_CLOUD, ACCESS_MODE_LOCAL, CONF_ACCESS_MODE, DOMAIN
from .flows.cloud import CloudConfigFlowMixin
from .flows.discovery import DiscoveryConfigFlowMixin
from .flows.local import LocalConfigFlowMixin
from .flows.options import UradmonitorOptionsFlow


class UradmonitorConfigFlow(
    DiscoveryConfigFlowMixin,
    LocalConfigFlowMixin,
    CloudConfigFlowMixin,
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Route the initial source selection to a domain-specific flow."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(
        _config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the source polling options flow."""
        return UradmonitorOptionsFlow()

    def __init__(self) -> None:
        """Initialize the source flows."""
        self._cloud_client = None
        self._cloud_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Choose the transport-specific setup flow."""
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
