"""Sensor platform for uRADMonitor."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import UradmonitorCoordinator

_LOGGER = logging.getLogger(__name__)

_SENSOR_DEFINITIONS: dict[
    str, tuple[str | None, SensorDeviceClass | None, str | None]
] = {
    # uRADMonitor reports radiation as CPM. The established integration
    # convention converts it to an approximate µSv/h value using cpm / 100.
    "cpm": ("µSv/h", None, "mdi:radioactive"),
    "temperature": (
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        None,
    ),
    "humidity": (PERCENTAGE, SensorDeviceClass.HUMIDITY, None),
    "pressure": ("hPa", SensorDeviceClass.PRESSURE, None),
    "voc": ("Ω", None, "mdi:air-filter"),
    "vocaqi": (None, SensorDeviceClass.AQI, None),
    "co2": ("ppm", SensorDeviceClass.CO2, None),
    # Cloud responses use ppb; local /j responses use ppm and are converted
    # in native_value so both transports expose the same entity unit.
    "ch2o": ("ppb", None, "mdi:flask-outline"),
    "pm1": ("µg/m³", SensorDeviceClass.PM1, None),
    "pm25": ("µg/m³", SensorDeviceClass.PM25, None),
    "pm10": ("µg/m³", SensorDeviceClass.PM10, None),
    "o3": ("ppb", SensorDeviceClass.OZONE, None),
    "noise": ("dB", SensorDeviceClass.SOUND_PRESSURE, None),
    "signal": ("dBm", SensorDeviceClass.SIGNAL_STRENGTH, None),
    "voltage": ("V", SensorDeviceClass.VOLTAGE, None),
    "duty": ("‰", None, None),
    "uptime": ("s", SensorDeviceClass.DURATION, "mdi:timer-outline"),
}

# These values describe the device or its operation rather than the monitored
# environment. Keeping them as diagnostic entities prevents them from being
# mixed with the primary measurement sensors in Home Assistant.
_DIAGNOSTIC_SENSORS = {"duty", "signal", "uptime", "voltage"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for one uRADMonitor config entry."""
    coordinators: dict[str, UradmonitorCoordinator] = hass.data[DOMAIN][
        "source_coordinators"
    ][entry.entry_id]
    device_id = str(entry.data[CONF_DEVICE_ID])
    entities = []
    for source, coordinator in coordinators.items():
        data = coordinator.device_data(device_id)
        entities.extend(
            UradmonitorSensor(coordinator, entry, device_id, source, key, *definition)
            for key, definition in _SENSOR_DEFINITIONS.items()
            if key in data
        )
    _LOGGER.debug(
        "Creating %d UradMonitor sensor(s) for %s: %s",
        len(entities),
        device_id,
        [entity.key for entity in entities],
    )
    async_add_entities(entities)


class UradmonitorSensor(CoordinatorEntity[UradmonitorCoordinator], SensorEntity):
    """Expose one normalized uRADMonitor measurement."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UradmonitorCoordinator,
        entry: ConfigEntry,
        device_id: str,
        source: str,
        key: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        icon: str | None,
    ) -> None:
        """Initialize a measurement sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.device_id = device_id
        self.source = source
        self.key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{device_id}_{source}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        if key in _DIAGNOSTIC_SENSORS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = {"identifiers": {(DOMAIN, f"{device_id}_{source}")}}

    @property
    def native_value(self) -> float | None:
        """Return the current numeric measurement."""
        value: Any = self.coordinator.device_data(self.device_id).get(self.key)
        if value is None:
            return None
        try:
            numeric_value = float(value)
        except TypeError, ValueError:
            _LOGGER.warning(
                "Invalid %s value for UradMonitor %s: %r",
                self.key,
                self.device_id,
                value,
            )
            return None
        if (
            self.key == "ch2o"
            and not getattr(self.coordinator, "units_normalized", False)
            and not self.coordinator.cloud
        ):
            numeric_value *= 1000
        elif self.key == "cpm":
            numeric_value /= 100
        elif self.key == "pressure":
            numeric_value /= 100
        return numeric_value

    @property
    def available(self) -> bool:
        """Return whether the selected device has fresh data."""
        return super().available and self.key in self.coordinator.device_data(
            self.device_id
        )
