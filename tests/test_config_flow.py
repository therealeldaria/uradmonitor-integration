"""Tests for the uradmonitor config flow."""

from custom_components.uradmonitor.config_flow import UradmonitorConfigFlow
from custom_components.uradmonitor.const import (
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_HOST,
    DOMAIN,
)
from custom_components.uradmonitor.models import get_model


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


def test_device_name_is_device_id_for_all_access_modes():
    """The stable device ID is used as the Home Assistant device name."""
    assert UradmonitorConfigFlow._device_name("5E6F7081") == "5E6F7081"


def test_known_model_mappings():
    """Known detector and hardware combinations resolve to their model."""
    assert get_model("SBM20", 109) == "Model A"
    assert get_model("SI29BG", 104) == "Model A3"
    assert get_model("SI29BG", 110) == "Model A3"


def test_unknown_model_mapping_is_explicit():
    """New hardware combinations remain visible as unknown."""
    assert get_model("unknown", "unknown") == "Unknown"


def test_local_device_id_is_read_from_data_object():
    """The local JSON endpoint returns the ID inside its data object."""
    response = {
        "data": {
            "id": "5E6F7081",
            "type": "8",
            "detector": "SI29BG",
            "temperature": 26.70,
        }
    }
    assert UradmonitorConfigFlow._local_device_id(response) == "5E6F7081"


def test_local_device_id_supports_top_level_fallback():
    """A top-level ID remains supported for alternate local responses."""
    assert UradmonitorConfigFlow._local_device_id({"id": "5E6F7081"}) == "5E6F7081"
