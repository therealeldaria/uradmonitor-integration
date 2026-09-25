"""Local-device setup flow."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..api.client import UradmonitorApiClient, UradmonitorApiError
from ..api.local_templates import local_json_metadata
from ..const import (
    ACCESS_MODE_LOCAL,
    CONF_DEVICE_ID,
    CONF_HARDWARE_VERSION,
    CONF_HOST,
    CONF_PORT,
    CONF_SOURCES,
)
from ..models import device_name, get_supported_device
from .common import add_source_to_existing, configured_entry

_LOGGER = logging.getLogger(__name__)


class LocalConfigFlowMixin:
    """Provide local transport setup to the main config flow."""

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure a device using its local API."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = UradmonitorApiClient(async_get_clientsession(self.hass))
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, 80)
            try:
                local_data = await client.async_get_local_data(host, port)
            except UradmonitorApiError:
                _LOGGER.warning(
                    "Unable to retrieve local JSON data from %s:%s", host, port
                )
                return self._show_local_form(user_input, "cannot_connect")

            device_type = self._local_device_type(local_data)
            definition = get_supported_device(device_type)
            if definition is None:
                _LOGGER.error(
                    "Unsupported local UradMonitor device type %s at %s:%s",
                    device_type,
                    host,
                    port,
                )
                errors["base"] = "unsupported_device"
                metadata = {}
            else:
                metadata = local_json_metadata(local_data)
                try:
                    html_metadata = await client.async_get_local_metadata(
                        host, port, definition.metadata_template
                    )
                except UradmonitorApiError:
                    _LOGGER.warning(
                        "Unable to retrieve optional metadata from local "
                        "UradMonitor at %s:%s",
                        host,
                        port,
                    )
                else:
                    metadata = {**metadata, **html_metadata}

            device_id = self._local_device_id(local_data)
            if not device_id and not errors:
                _LOGGER.error("Local UradMonitor response did not contain a device ID")
                errors["base"] = "invalid_response"
            elif device_id and not errors:
                await self.async_set_unique_id(device_id)
                source = {CONF_HOST: host, CONF_PORT: port}
                existing = configured_entry(self, device_id)
                if existing is not None:
                    return add_source_to_existing(
                        self, existing, ACCESS_MODE_LOCAL, source, metadata
                    )
                return self.async_create_entry(
                    title=device_name(definition, metadata.get(CONF_HARDWARE_VERSION)),
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_SOURCES: {ACCESS_MODE_LOCAL: source},
                        **metadata,
                    },
                )

        return self._show_local_form(user_input, errors.get("base"))

    def _show_local_form(
        self, user_input: dict[str, Any] | None, error: str | None = None
    ) -> config_entries.FlowResult:
        """Show the local connection form."""
        host = user_input.get(CONF_HOST) if user_input else None
        host_field = (
            vol.Required(CONF_HOST, default=host)
            if host
            else vol.Required(CONF_HOST)
        )
        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    host_field: str,
                    vol.Optional(
                        CONF_PORT,
                        default=user_input.get(CONF_PORT, 80) if user_input else 80,
                    ): vol.Coerce(int),
                }
            ),
            errors={"base": error} if error else {},
            description_placeholders={
                "host": str(user_input.get(CONF_HOST, "<device-host>")
                if user_input
                else "<device-host>")
            },
        )

    @staticmethod
    def _local_device_id(data: dict[str, Any]) -> str | None:
        """Extract the device ID from a local JSON response."""
        device_id = data.get("id")
        if device_id is None and isinstance(data.get("data"), dict):
            device_id = data["data"].get("id")
        return str(device_id) if device_id is not None else None

    @staticmethod
    def _local_device_type(data: dict[str, Any]) -> str | None:
        """Extract the device type used to select a local definition."""
        payload = data.get("data") if isinstance(data.get("data"), dict) else data
        device_type = payload.get("type")
        return str(device_type) if device_type is not None else None
