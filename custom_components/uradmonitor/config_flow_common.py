"""Shared config-flow operations for uRADMonitor sources."""

from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PORT,
    CONF_SOURCES,
    DOMAIN,
)


def configured_entry(flow: Any, device_id: str) -> ConfigEntry | None:
    """Find an existing entry for a physical device."""
    return next(
        (
            entry
            for entry in flow.hass.config_entries.async_entries(DOMAIN)
            if str(entry.unique_id or entry.data.get(CONF_DEVICE_ID)) == device_id
        ),
        None,
    )


def entry_sources(entry: ConfigEntry) -> dict[str, dict[str, Any]]:
    """Return source settings, including legacy entries."""
    if entry.data.get(CONF_SOURCES):
        return {key: dict(value) for key, value in entry.data[CONF_SOURCES].items()}
    mode = entry.data.get(CONF_ACCESS_MODE)
    if mode == ACCESS_MODE_LOCAL:
        return {
            ACCESS_MODE_LOCAL: {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data.get(CONF_PORT, 80),
            }
        }
    return {
        ACCESS_MODE_CLOUD: {
            CONF_CLOUD_USER_ID: entry.data[CONF_CLOUD_USER_ID],
            CONF_CLOUD_USER_KEY: entry.data[CONF_CLOUD_USER_KEY],
        }
    }


def add_source_to_existing(
    flow: Any,
    entry: ConfigEntry,
    mode: str,
    source: dict[str, Any],
    metadata: dict[str, Any],
) -> Any:
    """Add a second transport source to an existing device entry."""
    sources = entry_sources(entry)
    if mode in sources:
        return flow.async_abort(reason="already_configured")
    data = dict(entry.data)
    for key in (
        CONF_ACCESS_MODE,
        CONF_HOST,
        CONF_PORT,
        CONF_CLOUD_USER_ID,
        CONF_CLOUD_USER_KEY,
    ):
        data.pop(key, None)
    sources[mode] = source
    data[CONF_SOURCES] = sources
    for key, value in metadata.items():
        if mode == ACCESS_MODE_LOCAL:
            data[key] = value
        else:
            data.setdefault(key, value)
    return flow.async_update_reload_and_abort(entry, data=data, reason="source_added")
