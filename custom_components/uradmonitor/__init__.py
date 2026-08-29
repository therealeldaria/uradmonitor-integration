"""The uradmonitor integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_DETECTOR,
    CONF_DEVICE_ID,
    CONF_HARDWARE_VERSION,
    CONF_SOFTWARE_VERSION,
    DOMAIN,
    PLATFORMS,
)
from .models import get_model

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
