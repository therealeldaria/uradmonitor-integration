"""Zeroconf discovery for local UradMonitor devices."""

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ..api.client import UradmonitorApiClient, UradmonitorApiError
from ..const import CONF_HOST, CONF_PORT
from .common import configured_entry

_SERVICE_SUFFIX = "._http._tcp.local."
_SERVICE_PREFIX = "uradmonitor-"
_DISCOVERY_RETRIES = 6
_DISCOVERY_RETRY_DELAY = 30

_LOGGER = logging.getLogger(__name__)


def is_uradmonitor_service(discovery_info: ZeroconfServiceInfo) -> bool:
    """Return whether an HTTP mDNS service belongs to an UradMonitor."""
    name = str(getattr(discovery_info, "name", "")).lower().rstrip(".")
    service_name = name.removesuffix(_SERVICE_SUFFIX.rstrip("."))
    return service_name.startswith(_SERVICE_PREFIX)


def discovered_local_source(discovery_info: ZeroconfServiceInfo) -> dict[str, Any]:
    """Convert Zeroconf information into local-flow input."""
    host = getattr(discovery_info, "ip_address", None)
    if not host:
        addresses = getattr(discovery_info, "addresses", ())
        host = next((str(address) for address in addresses), None)
    if not host:
        host = str(getattr(discovery_info, "host", "")).rstrip(".")
    return {
        CONF_HOST: str(host),
        CONF_PORT: int(getattr(discovery_info, "port", 80) or 80),
    }


def discovered_local_unique_id(discovery_info: ZeroconfServiceInfo) -> str:
    """Return a stable temporary ID for an in-progress discovery flow."""
    source = discovered_local_source(discovery_info)
    return f"{source[CONF_HOST]}:{source[CONF_PORT]}"


class DiscoveryConfigFlowMixin:
    """Provide Zeroconf discovery for local UradMonitor devices."""

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> config_entries.FlowResult:
        """Handle an HTTP service announced by an UradMonitor."""
        if not is_uradmonitor_service(discovery_info):
            return self.async_abort(reason="not_uradmonitor")
        source = discovered_local_source(discovery_info)
        await self.async_set_unique_id(discovered_local_unique_id(discovery_info))
        local_data: dict[str, Any] | None = None
        for attempt in range(_DISCOVERY_RETRIES):
            try:
                client = UradmonitorApiClient(async_get_clientsession(self.hass))
                local_data = await client.async_get_local_data(
                    source[CONF_HOST], source[CONF_PORT]
                )
            except UradmonitorApiError:
                if attempt == _DISCOVERY_RETRIES - 1:
                    self._discovery_error = "cannot_connect"
                    self._discovery_host = str(source[CONF_HOST])
                    return await self.async_step_discovery_error()
                _LOGGER.debug(
                    "Discovered UradMonitor at %s is not ready; retrying (%s/%s)",
                    source[CONF_HOST],
                    attempt + 2,
                    _DISCOVERY_RETRIES,
                )
                await asyncio.sleep(_DISCOVERY_RETRY_DELAY)
                continue
            break

        device_id = self._local_device_id(local_data or {})
        if not device_id:
            self._discovery_error = "invalid_response"
            self._discovery_host = str(source[CONF_HOST])
            return await self.async_step_discovery_error()
        if configured_entry(self, device_id) is not None:
            return self.async_abort(reason="already_configured")

        self._discovered_source = source
        return await self.async_step_discovered_local()

    async def async_step_discovered_local(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Ask for confirmation before adding a discovered local device."""
        if user_input is not None:
            return await self.async_step_local(self._discovered_source)
        return self.async_show_form(
            step_id="discovered_local",
            data_schema=vol.Schema({}),
            description_placeholders={
                "host": str(self._discovered_source[CONF_HOST])
            },
        )

    async def async_step_discovery_error(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Show a discovery error without asking for the host again."""
        if user_input is not None:
            return self.async_abort(reason="discovery_error_dismissed")
        return self.async_show_form(
            step_id="discovery_error",
            data_schema=vol.Schema({}),
            errors={"base": self._discovery_error},
            description_placeholders={"host": self._discovery_host},
        )
