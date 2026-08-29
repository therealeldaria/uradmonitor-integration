"""The uradmonitor integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_DEVICE_ID, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


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
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, str(device_id))},
        name=entry.title,
        manufacturer="UradMonitor",
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a uradmonitor config entry."""
    _LOGGER.info("Unloading UradMonitor config entry %s", entry.entry_id)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
