"""Tests for the uradmonitor config flow."""

from custom_components.uradmonitor.api.local_templates import (
    LEGACY_A3_TEMPLATE,
    device_name,
    get_local_device_definition,
)
from custom_components.uradmonitor.config_flow import UradmonitorConfigFlow
from custom_components.uradmonitor.const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SOURCES,
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


def test_local_device_type_is_read_from_data_object():
    """The local JSON type selects the status-page template."""
    assert UradmonitorConfigFlow._local_device_type({"data": {"type": 8}}) == "8"


def test_local_device_type_supports_top_level_fallback():
    """Alternate local responses may put type at the top level."""
    assert UradmonitorConfigFlow._local_device_type({"type": "8"}) == "8"


def test_device_type_selects_a_named_definition_and_reusable_template():
    """The JSON type selects a device name and metadata template."""
    definition = get_local_device_definition(8)
    assert definition is not None
    assert definition.name == "A3"
    assert definition.metadata_template is LEGACY_A3_TEMPLATE
    assert device_name(definition, 104) == "A3-104"


def test_metadata_template_does_not_extract_sensor_values_or_identity():
    """HTML templates return static metadata only."""
    metadata = LEGACY_A3_TEMPLATE.parse_metadata(
        "<b>uRADMonitor 8200005B</b><br>type:8 hw:104 sw:124 SI29BG"
        "<hr>radiation:9CPM<br>temperature:19.73C"
    )
    assert metadata == {
        "device_type": "8",
        "hardware_version": "104",
        "software_version": "124",
        "detector": "SI29BG",
    }


def test_entry_sources_supports_legacy_local_entry():
    """Legacy local entries are readable before migration runs."""
    from types import SimpleNamespace

    entry = SimpleNamespace(
        data={
            CONF_ACCESS_MODE: ACCESS_MODE_LOCAL,
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 80,
        }
    )

    assert UradmonitorConfigFlow._entry_sources(entry) == {  # noqa: SLF001
        ACCESS_MODE_LOCAL: {CONF_HOST: "192.0.2.10", CONF_PORT: 80}
    }


def test_entry_sources_reads_combined_entry():
    """Combined entries expose both source configurations."""
    from types import SimpleNamespace

    sources = {
        ACCESS_MODE_LOCAL: {CONF_HOST: "192.0.2.10", CONF_PORT: 80},
        ACCESS_MODE_CLOUD: {
            CONF_CLOUD_USER_ID: "user",
            CONF_CLOUD_USER_KEY: "secret",
        },
    }
    entry = SimpleNamespace(data={CONF_SOURCES: sources})

    assert UradmonitorConfigFlow._entry_sources(entry) == sources  # noqa: SLF001
