"""The uradmonitor integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api.client import UradmonitorApiClient
from .const import (
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DETECTOR,
    CONF_DEVICE_ID,
    CONF_HARDWARE_VERSION,
    CONF_POLL_INTERVAL,
    CONF_SOFTWARE_VERSION,
    DEFAULT_CLOUD_POLL_INTERVAL,
    DEFAULT_LOCAL_POLL_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import UradmonitorCoordinator, is_cloud_entry
from .models import get_model

_LOGGER = logging.getLogger(__name__)
_COORDINATORS = "coordinators"
_CLOUD_COORDINATORS = "cloud_coordinators"


def _poll_interval(entry: ConfigEntry) -> int:
    """Return the configured polling interval for an entry."""
    default = (
        DEFAULT_CLOUD_POLL_INTERVAL
        if is_cloud_entry(entry)
        else DEFAULT_LOCAL_POLL_INTERVAL
    )
    return int(entry.options.get(CONF_POLL_INTERVAL, default))


def _cloud_key(entry: ConfigEntry) -> tuple[str, str]:
    """Return the exact credentials key used for cloud sharing."""
    return (
        str(entry.data[CONF_CLOUD_USER_ID]),
        str(entry.data[CONF_CLOUD_USER_KEY]),
    )


async def _async_get_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> UradmonitorCoordinator:
    """Create or reuse a coordinator for a config entry."""
    domain_data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    if is_cloud_entry(entry):
        cloud_coordinators: dict[tuple[str, str], dict[str, Any]] = (
            domain_data.setdefault(_CLOUD_COORDINATORS, {})
        )
        key = _cloud_key(entry)
        shared = cloud_coordinators.get(key)
        if shared is None:
            client = UradmonitorApiClient(
                async_get_clientsession(hass),
                user_id=key[0],
                user_key=key[1],
            )
            coordinator = UradmonitorCoordinator(
                hass,
                entry,
                client,
                _poll_interval(entry),
                cloud=True,
            )
            shared = {"coordinator": coordinator, "entries": set()}
            cloud_coordinators[key] = shared
        coordinator = shared["coordinator"]
        shared["entries"].add(entry.entry_id)
        coordinator.set_update_interval(_poll_interval(entry))
    else:
        client = UradmonitorApiClient(async_get_clientsession(hass))
        coordinator = UradmonitorCoordinator(
            hass,
            entry,
            client,
            _poll_interval(entry),
            cloud=False,
        )
        domain_data.setdefault(_COORDINATORS, {})[entry.entry_id] = coordinator

    if coordinator.data is None:
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            raise ConfigEntryNotReady(str(err)) from err
    return coordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up uradmonitor from a config entry."""
    _LOGGER.info("Setting up UradMonitor config entry %s", entry.entry_id)
    device_id = entry.data.get(CONF_DEVICE_ID) or entry.unique_id
    if not device_id:
        _LOGGER.error(
            "Cannot register UradMonitor device for config entry %s: no device ID",
            entry.entry_id,
        )
        return False

    device_registry = dr.async_get(hass)
    detector = entry.data.get(CONF_DETECTOR)
    model = get_model(detector, entry.data.get(CONF_HARDWARE_VERSION))
    if detector:
        model = f"{model} ({detector})"
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(device_id))},
        name=str(device_id),
        manufacturer="uRADMonitor",
        model=model,
        hw_version=entry.data.get(CONF_HARDWARE_VERSION),
        sw_version=entry.data.get(CONF_SOFTWARE_VERSION),
    )
    if not device.name_by_user and device.name != str(device_id):
        device_registry.async_update_device(device.id, name=str(device_id))
    coordinator = await _async_get_coordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(_COORDINATORS, {})[entry.entry_id] = (
        coordinator
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a uradmonitor config entry."""
    _LOGGER.info("Unloading UradMonitor config entry %s", entry.entry_id)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        domain_data = hass.data[DOMAIN]
        coordinator = domain_data.get(_COORDINATORS, {}).pop(entry.entry_id, None)
        if is_cloud_entry(entry):
            key = _cloud_key(entry)
            shared = domain_data.get(_CLOUD_COORDINATORS, {}).get(key)
            if shared is not None:
                shared["entries"].discard(entry.entry_id)
                if not shared["entries"]:
                    await shared["coordinator"].async_shutdown()
                    domain_data[_CLOUD_COORDINATORS].pop(key, None)
        else:
            if coordinator is not None:
                await coordinator.async_shutdown()
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload an entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
