"""Tests for the uradmonitor config flow."""

from custom_components.uradmonitor.api.local_templates import A3_2016_TEMPLATE
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
from custom_components.uradmonitor.flows.cloud import CloudConfigFlowMixin
from custom_components.uradmonitor.flows.common import entry_sources
from custom_components.uradmonitor.flows.discovery import (
    discovered_local_source,
    is_uradmonitor_service,
)
from custom_components.uradmonitor.flows.local import LocalConfigFlowMixin
from custom_components.uradmonitor.models import (
    device_name,
    get_supported_device,
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
        CloudConfigFlowMixin._device_label(  # noqa: SLF001
            {"id": "82000466", "note": "Living room", "city": "Fyrunga"}
        )
        == "Living room (ID: 82000466)"
    )


def test_cloud_device_label_falls_back_to_city():
    """The city is used when a cloud device has no note."""
    assert (
        CloudConfigFlowMixin._device_label(  # noqa: SLF001
            {"id": "82000466", "city": "Fyrunga"}
        )
        == "Fyrunga (ID: 82000466)"
    )


def test_cloud_device_label_has_generic_fallback():
    """A generic name is used when no location is available."""
    assert CloudConfigFlowMixin._device_label({"id": "82000466"}) == (
        "UradMonitor (ID: 82000466)"
    )


def test_device_name_is_device_id_for_all_access_modes():
    """The stable device ID is used as the Home Assistant device name."""
    assert CloudConfigFlowMixin._device_name("5E6F7081") == "5E6F7081"


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
    assert LocalConfigFlowMixin._local_device_id(response) == "5E6F7081"


def test_local_device_id_supports_top_level_fallback():
    """A top-level ID remains supported for alternate local responses."""
    assert LocalConfigFlowMixin._local_device_id({"id": "5E6F7081"}) == "5E6F7081"


def test_local_device_type_is_read_from_data_object():
    """The local JSON type selects the status-page template."""
    assert LocalConfigFlowMixin._local_device_type({"data": {"type": 8}}) == "8"


def test_local_device_type_supports_top_level_fallback():
    """Alternate local responses may put type at the top level."""
    assert LocalConfigFlowMixin._local_device_type({"type": "8"}) == "8"


def test_zeroconf_identifies_uradmonitor_http_service():
    """The device's mDNS service name identifies it as an UradMonitor."""
    from ipaddress import IPv4Address
    from types import SimpleNamespace

    info = SimpleNamespace(
        name="uRADMonitor-36._http._tcp.local.",
        ip_address=IPv4Address("192.168.30.7"),
        port=80,
    )

    assert is_uradmonitor_service(info)
    assert discovered_local_source(info) == {CONF_HOST: "192.168.30.7", CONF_PORT: 80}


def test_zeroconf_ignores_other_http_services():
    """Other HTTP services must not start the UradMonitor flow."""
    from types import SimpleNamespace

    assert not is_uradmonitor_service(
        SimpleNamespace(name="printer._http._tcp.local.")
    )


def test_local_form_preserves_discovered_host_and_port():
    """Discovery values remain filled in when local validation fails."""
    class Flow(LocalConfigFlowMixin):
        def async_show_form(self, **kwargs):
            return kwargs

    form = Flow()._show_local_form(  # noqa: SLF001
        {CONF_HOST: "192.168.30.7", CONF_PORT: 8080}, "unsupported_device"
    )

    assert form["data_schema"]({}) == {
        CONF_HOST: "192.168.30.7",
        CONF_PORT: 8080,
    }


def test_device_type_selects_a_named_definition_and_reusable_template():
    """The JSON type selects a device name and metadata template."""
    definition = get_supported_device(8)
    assert definition is not None
    assert definition.name == "A3"
    assert definition.metadata_template is A3_2016_TEMPLATE
    assert device_name(definition, 104) == "A3-104"


def test_metadata_template_does_not_extract_sensor_values_or_identity():
    """HTML templates return static metadata only."""
    metadata = A3_2016_TEMPLATE.parse_metadata(
        "<b>uRADMonitor 8200005B</b><br>type:8 hw:104 sw:124 SI29BG"
        "<hr>radiation:9CPM<br>temperature:19.73C"
    )
    assert metadata == {
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

    assert entry_sources(entry) == {
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

    assert entry_sources(entry) == sources
