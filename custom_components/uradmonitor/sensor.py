"""Sensor platform for uradmonitor."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for one uradmonitor config entry."""
    # No measurements are exposed until the API schema is verified.
    async_add_entities([])


class UradmonitorSensor(SensorEntity):
    """Base sensor for a normalized uradmonitor measurement."""
