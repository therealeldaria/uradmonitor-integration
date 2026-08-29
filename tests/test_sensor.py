"""Tests for the uradmonitor sensor platform."""

from custom_components.uradmonitor.const import PLATFORMS


def test_sensor_platform_is_registered():
    """The integration registers the sensor platform."""
    assert "sensor" in PLATFORMS
