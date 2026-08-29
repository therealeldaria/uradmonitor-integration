"""Tests for local/cloud coordinator data merging."""

from custom_components.uradmonitor.coordinator import merge_device_data


def test_local_values_override_cloud_and_cloud_only_values_are_kept():
    """Local readings win while cloud-only readings remain available."""
    merged = merge_device_data(
        "8200005B",
        local_data={"temperature": 21, "ch2o": 0.02},
        cloud_data={
            "8200005B": {"temperature": 22, "pm10": 4, "ch2o": 30},
        },
    )

    assert merged == {"temperature": 21, "pm10": 4, "ch2o": 20}


def test_cloud_is_used_when_local_is_unavailable():
    """Cloud data is a fallback when local polling fails."""
    assert merge_device_data(
        "8200005B",
        local_data={"temperature": 21},
        cloud_data={"8200005B": {"temperature": 22, "pm10": 4}},
        local_available=False,
    ) == {"temperature": 22, "pm10": 4}


def test_local_only_data_is_supported():
    """A combined merge also works before cloud is configured."""
    assert merge_device_data(
        "8200005B", local_data={"temperature": 21}, cloud_available=False
    ) == {"temperature": 21}
