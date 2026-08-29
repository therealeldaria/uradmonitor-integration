"""Tests for the uradmonitor config flow."""

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
