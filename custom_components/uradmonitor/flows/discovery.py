"""Zeroconf discovery for local UradMonitor devices."""

from typing import Any

from homeassistant import config_entries
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ..const import CONF_HOST, CONF_PORT

_SERVICE_SUFFIX = "._http._tcp.local."
_SERVICE_PREFIX = "uradmonitor-"


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
        CONF_HOST: host,
        CONF_PORT: int(getattr(discovery_info, "port", 80) or 80),
    }


class DiscoveryConfigFlowMixin:
    """Provide Zeroconf discovery for local UradMonitor devices."""

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> config_entries.FlowResult:
        """Handle an HTTP service announced by an UradMonitor."""
        if not is_uradmonitor_service(discovery_info):
            return self.async_abort(reason="not_uradmonitor")
        return await self.async_step_local(discovered_local_source(discovery_info))
