"""Tests for the uradmonitor config flow."""

from custom_components.uradmonitor.config_flow import UradmonitorConfigFlow
from custom_components.uradmonitor.const import (
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_HOST,
    DOMAIN,
)


def test_local_access_mode_constants():
    """The initial configuration vocabulary is stable."""
    assert DOMAIN == "uradmonitor"
    assert ACCESS_MODE_LOCAL == "local"
    assert CONF_ACCESS_MODE == "access_mode"
    assert CONF_HOST == "host"


def test_cloud_device_label_prefers_note_and_includes_id():
    """A cloud device note is displayed together with its ID."""
    assert (
        UradmonitorConfigFlow._device_label(  # noqa: SLF001
            {"id": "82000466", "note": "Living room", "city": "Fyrunga"}
        )
        == "Living room (ID: 82000466)"
    )


def test_cloud_device_label_falls_back_to_city():
    """The city is used when a cloud device has no note."""
    assert (
        UradmonitorConfigFlow._device_label(  # noqa: SLF001
            {"id": "82000466", "city": "Fyrunga"}
        )
        == "Fyrunga (ID: 82000466)"
    )


def test_cloud_device_label_has_generic_fallback():
    """A generic name is used when no location is available."""
    assert UradmonitorConfigFlow._device_label({"id": "82000466"}) == (
        "UradMonitor (ID: 82000466)"
    )
