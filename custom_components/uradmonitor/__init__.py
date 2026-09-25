"""The uradmonitor integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api.client import UradmonitorApiClient, UradmonitorApiError
from .const import (
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_POLL_INTERVAL,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_DETECTOR,
    CONF_DEVICE_ID,
    CONF_DEVICE_TYPE,
    CONF_HARDWARE_VERSION,
    CONF_HOST,
    CONF_LOCAL_POLL_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_SOFTWARE_VERSION,
    CONF_SOURCES,
    DEFAULT_CLOUD_POLL_INTERVAL,
    DEFAULT_LOCAL_POLL_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import UradmonitorCoordinator, has_local_source, is_cloud_entry
from .models import device_name, get_supported_device

_LOGGER = logging.getLogger(__name__)
_CLOUD_COORDINATORS = "cloud_coordinators"
_SOURCE_COORDINATORS = "source_coordinators"


def _poll_interval(entry: ConfigEntry, *, cloud: bool) -> int:
    """Return the configured polling interval for an entry."""
    option = CONF_CLOUD_POLL_INTERVAL if cloud else CONF_LOCAL_POLL_INTERVAL
    default = DEFAULT_CLOUD_POLL_INTERVAL if cloud else DEFAULT_LOCAL_POLL_INTERVAL
    return int(
        entry.options.get(option, entry.options.get(CONF_POLL_INTERVAL, default))
    )


def _cloud_key(entry: ConfigEntry) -> tuple[str, str]:
    """Return the exact credentials key used for cloud sharing."""
    cloud = entry.data.get("sources", {}).get("cloud", {})
    return (
        str(cloud.get(CONF_CLOUD_USER_ID, entry.data.get(CONF_CLOUD_USER_ID))),
        str(cloud.get(CONF_CLOUD_USER_KEY, entry.data.get(CONF_CLOUD_USER_KEY))),
    )


async def _async_get_coordinators(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, UradmonitorCoordinator]:
    """Create or reuse source coordinators for a config entry."""
    domain_data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    sources: dict[str, UradmonitorCoordinator] = {}
    if has_local_source(entry):
        client = UradmonitorApiClient(async_get_clientsession(hass))
        sources["local"] = UradmonitorCoordinator(
            hass,
            entry,
            client,
            _poll_interval(entry, cloud=False),
            cloud=False,
        )

    if is_cloud_entry(entry):
        cloud_coordinators: dict[tuple[str, str], dict[str, Any]] = (
            domain_data.setdefault(_CLOUD_COORDINATORS, {})
        )
        key = _cloud_key(entry)
        shared = cloud_coordinators.get(key)
        if shared is None:
            client = UradmonitorApiClient(
                async_get_clientsession(hass),
                user_id=key[0],
                user_key=key[1],
            )
            coordinator = UradmonitorCoordinator(
                hass,
                entry,
                client,
                _poll_interval(entry, cloud=True),
                cloud=True,
            )
            shared = {"coordinator": coordinator, "entries": set()}
            cloud_coordinators[key] = shared
        coordinator: UradmonitorCoordinator = shared["coordinator"]
        shared["entries"].add(entry.entry_id)
        coordinator.set_update_interval(_poll_interval(entry, cloud=True))
        sources["cloud"] = coordinator

    if not sources:
        raise ConfigEntryNotReady("No UradMonitor source is configured")

    for source in sources.values():
        if source.data is None:
            try:
                if len(sources) == 1:
                    await source.async_config_entry_first_refresh()
                else:
                    # Multiple sources must initialize independently. One
                    # temporarily unavailable transport must not prevent the
                    # other source from providing its own entities.
                    await source.async_refresh()
            except UpdateFailed as err:
                _LOGGER.warning(
                    "UradMonitor source unavailable during setup for %s: %s",
                    entry.data.get(CONF_DEVICE_ID),
                    err,
                )
            if not source.last_update_success:
                _LOGGER.warning(
                    "UradMonitor source unavailable during setup for %s: %s",
                    entry.data.get(CONF_DEVICE_ID),
                    source.last_exception,
                )

    domain_data.setdefault(_SOURCE_COORDINATORS, {})[entry.entry_id] = sources
    if not any(source.data for source in sources.values()):
        raise ConfigEntryNotReady("No UradMonitor source returned data")
    return sources


async def _async_refresh_local_metadata(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Refresh static HTML metadata once when a local entry starts."""
    if not has_local_source(entry):
        return
    definition = get_supported_device(entry.data.get(CONF_DEVICE_TYPE))
    if definition is None:
        return
    source = entry.data.get(CONF_SOURCES, {}).get(ACCESS_MODE_LOCAL, {})
    client = UradmonitorApiClient(async_get_clientsession(hass))
    try:
        metadata = await client.async_get_local_metadata(
            source.get(CONF_HOST, entry.data.get(CONF_HOST)),
            source.get(CONF_PORT, entry.data.get(CONF_PORT, 80)),
            definition.metadata_template,
        )
    except UradmonitorApiError as err:
        _LOGGER.debug("Unable to refresh optional local metadata: %s", err)
        return
    changed = {
        key: value
        for key, value in metadata.items()
        if entry.data.get(key) != value
    }
    if changed:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, **changed}
        )


def _source_identifier(device_id: str, source: str) -> str:
    """Return the Home Assistant identifier for one transport."""
    return f"{device_id}_{source}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up uradmonitor from a config entry."""
    _LOGGER.info("Setting up UradMonitor config entry %s", entry.entry_id)
    device_id = entry.data.get(CONF_DEVICE_ID) or entry.unique_id
    if not device_id:
        _LOGGER.error(
            "Cannot register UradMonitor device for config entry %s: no device ID",
            entry.entry_id,
        )
        return False

    device_registry = dr.async_get(hass)
    await _async_refresh_local_metadata(hass, entry)
    coordinators = await _async_get_coordinators(hass, entry)
    detector = entry.data.get(CONF_DETECTOR)
    definition = get_supported_device(entry.data.get(CONF_DEVICE_TYPE))
    model = (
        device_name(definition, entry.data.get(CONF_HARDWARE_VERSION))
        if definition
        else "Unknown"
    )
    if detector:
        model = f"{model} ({detector})"
    for source in coordinators:
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, _source_identifier(str(device_id), source))},
            name=f"{device_id} ({source.title()})",
            manufacturer="uRADMonitor",
            model=model,
            hw_version=entry.data.get(CONF_HARDWARE_VERSION),
            sw_version=entry.data.get(CONF_SOFTWARE_VERSION),
            serial_number=str(device_id),
        )
        if not device.name_by_user and device.name != f"{device_id} ({source.title()})":
            device_registry.async_update_device(
                device.id, name=f"{device_id} ({source.title()})"
            )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy single-source entries to the combined format."""
    if entry.version >= 2:
        return True

    mode = entry.data.get(CONF_ACCESS_MODE)
    source: dict[str, Any]
    if mode == "local":
        source = {
            "local": {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data.get(CONF_PORT, 80),
            }
        }
    else:
        source = {
            "cloud": {
                CONF_CLOUD_USER_ID: entry.data[CONF_CLOUD_USER_ID],
                CONF_CLOUD_USER_KEY: entry.data[CONF_CLOUD_USER_KEY],
            }
        }
    data = {
        key: value
        for key, value in entry.data.items()
        if key
        not in {
            CONF_ACCESS_MODE,
            CONF_HOST,
            CONF_PORT,
            CONF_CLOUD_USER_ID,
            CONF_CLOUD_USER_KEY,
        }
    }
    data[CONF_SOURCES] = source
    hass.config_entries.async_update_entry(entry, data=data, version=2)
    _LOGGER.info("Migrated UradMonitor config entry %s to version 2", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a uradmonitor config entry."""
    _LOGGER.info("Unloading UradMonitor config entry %s", entry.entry_id)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        domain_data = hass.data[DOMAIN]
        sources = domain_data.get(_SOURCE_COORDINATORS, {}).pop(entry.entry_id, {})
        if is_cloud_entry(entry):
            key = _cloud_key(entry)
            shared = domain_data.get(_CLOUD_COORDINATORS, {}).get(key)
            if shared is not None:
                shared["entries"].discard(entry.entry_id)
                if not shared["entries"]:
                    await shared["coordinator"].async_shutdown()
                    domain_data[_CLOUD_COORDINATORS].pop(key, None)
        if "local" in sources:
            await sources["local"].async_shutdown()
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload an entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
