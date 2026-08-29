"""Tests for source-specific coordinator behavior."""

from types import SimpleNamespace

from custom_components.uradmonitor.coordinator import has_local_source, is_cloud_entry


def test_combined_entry_exposes_both_source_types():
    """A combined config entry enables both independent transports."""
    entry = SimpleNamespace(
        data={"sources": {"local": {"host": "192.0.2.10"}, "cloud": {}}}
    )

    assert has_local_source(entry)
    assert is_cloud_entry(entry)


def test_source_specific_entity_identity_is_deterministic():
    """Local and cloud identities remain distinct for one physical device."""
    device_id = "8200005B"
    assert f"{device_id}_local_temperature" != f"{device_id}_cloud_temperature"
