"""Config flow for uradmonitor."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api.client import UradmonitorApiClient, UradmonitorApiError
from .api.local_templates import (
    device_name,
    get_local_device_definition,
    local_json_metadata,
)
from .const import (
    ACCESS_MODE_CLOUD,
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
    POLL_INTERVAL_OPTIONS,
)
from .coordinator import is_cloud_entry

_LOGGER = logging.getLogger(__name__)


class UradmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a uradmonitor config flow."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(
        _config_entry: ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for polling settings."""
        return UradmonitorOptionsFlow()

    def __init__(self) -> None:
        """Initialize a config flow."""
        self._cloud_client: UradmonitorApiClient | None = None
        self._cloud_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup form."""
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_MODE, default=ACCESS_MODE_LOCAL): vol.In(
                    [ACCESS_MODE_LOCAL, ACCESS_MODE_CLOUD]
                ),
            }
        )
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        if user_input[CONF_ACCESS_MODE] == ACCESS_MODE_LOCAL:
            return await self.async_step_local()
        return await self.async_step_cloud()

    async def async_step_local(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure a device using its local API."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = UradmonitorApiClient(async_get_clientsession(self.hass))
            try:
                local_data = await client.async_get_local_data(
                    user_input[CONF_HOST], user_input.get(CONF_PORT, 80)
                )
            except UradmonitorApiError:
                _LOGGER.warning(
                    "Unable to retrieve local JSON data from "
                    "UradMonitor at %s:%s",
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, 80),
                )
                return self._show_local_form(user_input, "cannot_connect")

            device_type = self._local_device_type(local_data)
            definition = get_local_device_definition(device_type)
            if definition is None:
                _LOGGER.error(
                    "Unsupported local UradMonitor device type %s at %s:%s",
                    device_type,
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, 80),
                )
                errors["base"] = self._unsupported_device_error(
                    user_input[CONF_HOST]
                )
                metadata = {}
            else:
                metadata = local_json_metadata(local_data)
                try:
                    metadata = await client.async_get_local_metadata(
                        user_input[CONF_HOST],
                        user_input.get(CONF_PORT, 80),
                        definition.metadata_template,
                    )
                    metadata = {**local_json_metadata(local_data), **metadata}
                except UradmonitorApiError:
                    _LOGGER.warning(
                        "Unable to retrieve optional metadata from local "
                        "UradMonitor at %s:%s",
                        user_input[CONF_HOST],
                        user_input.get(CONF_PORT, 80),
                    )
                    metadata = local_json_metadata(local_data)

            device_id = self._local_device_id(local_data) if local_data else None

            if not device_id and not errors:
                _LOGGER.error("Local UradMonitor response did not contain a device ID")
                errors["base"] = "invalid_response"
            elif device_id and not errors:
                device_id = str(device_id)
                await self.async_set_unique_id(device_id)
                source = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input.get(CONF_PORT, 80),
                }
                existing = self._configured_entry(device_id)
                if existing is not None:
                    return self._add_source_to_existing(
                        existing, ACCESS_MODE_LOCAL, source, metadata
                    )
                return self.async_create_entry(
                    title=device_name(
                        definition, metadata.get(CONF_HARDWARE_VERSION)
                    ),
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_SOURCES: {ACCESS_MODE_LOCAL: source},
                        **metadata,
                    },
                )

        return self._show_local_form(user_input, errors.get("base"))

    def _show_local_form(
        self, user_input: dict[str, Any] | None, error: str | None = None
    ) -> config_entries.FlowResult:
        """Show the local form with an error that Home Assistant can translate."""
        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=80): vol.Coerce(int),
                }
            ),
            errors={"base": error} if error else {},
        )

    def _unsupported_device_error(self, host: str) -> str:
        """Return actionable plain-text guidance for an unknown device type."""
        if self.hass.config.language == "sv":
            return (
                "Den här enhetstypen stöds inte ännu. Lägg gärna upp svaren från "
                f"http://{host}/j och http://{host}/ i GitHub-ärendehanteringen: "
                "https://github.com/therealeldaria/uradmonitor-integration/issues. "
                "Ta bort publika IP-adresser eller annan känslig information vid behov."
            )
        return (
            "This device type is not supported yet. Please submit the responses "
            f"from http://{host}/j and http://{host}/ to the GitHub issue tracker: "
            "https://github.com/therealeldaria/uradmonitor-integration/issues. "
            "Redact public IP addresses or other sensitive information if needed."
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Authenticate with the cloud API and select one device."""
        errors: dict[str, str] = {}
        if user_input is not None and self._cloud_client is None:
            self._cloud_client = UradmonitorApiClient(
                async_get_clientsession(self.hass),
                user_id=user_input[CONF_CLOUD_USER_ID],
                user_key=user_input[CONF_CLOUD_USER_KEY],
            )
            try:
                self._cloud_devices = await self._cloud_client.async_get_devices()
            except UradmonitorApiError:
                _LOGGER.error(
                    "Unable to retrieve devices from the UradMonitor cloud API",
                    exc_info=True,
                )
                self._cloud_client = None
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_cloud_device()

        if self._cloud_client is not None:
            return await self.async_step_cloud_device(user_input)

        return self.async_show_form(
            step_id="cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLOUD_USER_ID): str,
                    vol.Required(CONF_CLOUD_USER_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_cloud_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select one device returned by the cloud API."""
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = next(
                device
                for device in self._cloud_devices
                if str(device.get("id")) == device_id
            )
            assert self._cloud_client is not None
            await self.async_set_unique_id(str(device_id))
            source = {
                CONF_CLOUD_USER_ID: self._cloud_client.user_id,
                CONF_CLOUD_USER_KEY: self._cloud_client.user_key,
            }
            existing = self._configured_entry(str(device_id))
            if existing is not None:
                return self._add_source_to_existing(
                    existing, ACCESS_MODE_CLOUD, source, self._cloud_metadata(device)
                )
            return self.async_create_entry(
                title=self._device_name(str(device_id)),
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_SOURCES: {ACCESS_MODE_CLOUD: source},
                    **self._cloud_metadata(device),
                },
            )

        options = [
            SelectOptionDict(value=str(device["id"]), label=self._device_label(device))
            for device in self._cloud_devices
            if device.get("id")
        ]
        if not options:
            return self.async_abort(reason="no_devices")
        return self.async_show_form(
            step_id="cloud_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
        )

    @staticmethod
    def _device_label(device: dict[str, Any]) -> str:
        """Return a useful label for a cloud device."""
        device_id = str(device["id"])
        name = device.get("note") or device.get("city") or "UradMonitor"
        return f"{name} (ID: {device_id})"

    @staticmethod
    def _device_name(device_id: str) -> str:
        """Return the default Home Assistant device name."""
        return device_id

    @staticmethod
    def _cloud_metadata(device: dict[str, Any]) -> dict[str, str]:
        """Extract shared metadata from a cloud device response."""
        metadata = {
            CONF_DEVICE_TYPE: device.get("type"),
            CONF_DETECTOR: device.get("detector"),
            CONF_HARDWARE_VERSION: device.get("versionhw"),
            CONF_SOFTWARE_VERSION: device.get("versionsw"),
        }
        return {key: str(value) for key, value in metadata.items() if value is not None}

    @staticmethod
    def _local_device_id(data: dict[str, Any]) -> str | None:
        """Extract the device ID from a local JSON response."""
        device_id = data.get("id")
        if device_id is None and isinstance(data.get("data"), dict):
            device_id = data["data"].get("id")
        return str(device_id) if device_id is not None else None

    @staticmethod
    def _local_device_type(data: dict[str, Any]) -> str | None:
        """Extract the device type used to select a local status template."""
        if isinstance(data.get("data"), dict):
            device_type = data["data"].get("type")
        else:
            device_type = data.get("type")
        return str(device_type) if device_type is not None else None

    def _configured_entry(self, device_id: str) -> ConfigEntry | None:
        """Find an existing entry for a physical device."""
        return next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if str(entry.unique_id or entry.data.get(CONF_DEVICE_ID)) == device_id
            ),
            None,
        )

    @staticmethod
    def _entry_sources(entry: ConfigEntry) -> dict[str, dict[str, Any]]:
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

    def _add_source_to_existing(
        self,
        entry: ConfigEntry,
        mode: str,
        source: dict[str, Any],
        metadata: dict[str, Any],
    ) -> config_entries.FlowResult:
        """Add a second source to an existing device entry."""
        sources = self._entry_sources(entry)
        if mode in sources:
            return self.async_abort(reason="already_configured")
        data = dict(entry.data)
        data.pop(CONF_ACCESS_MODE, None)
        data.pop(CONF_HOST, None)
        data.pop(CONF_PORT, None)
        data.pop(CONF_CLOUD_USER_ID, None)
        data.pop(CONF_CLOUD_USER_KEY, None)
        sources[mode] = source
        data[CONF_SOURCES] = sources
        for key, value in metadata.items():
            if mode == ACCESS_MODE_LOCAL:
                data[key] = value
            else:
                data.setdefault(key, value)
        return self.async_update_reload_and_abort(
            entry, data=data, reason="source_added"
        )


class UradmonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle polling interval changes."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage polling interval options."""
        config_entry = self.config_entry
        local = config_entry.data.get(CONF_SOURCES, {}).get(ACCESS_MODE_LOCAL)
        cloud = config_entry.data.get(CONF_SOURCES, {}).get(ACCESS_MODE_CLOUD)
        if not config_entry.data.get(CONF_SOURCES):
            local = config_entry.data.get(CONF_ACCESS_MODE) == ACCESS_MODE_LOCAL
            cloud = config_entry.data.get(CONF_ACCESS_MODE) == ACCESS_MODE_CLOUD
        if user_input is not None:
            options = dict(config_entry.options)
            options.update(
                {
                    key: int(value)
                    for key, value in user_input.items()
                    if value is not None
                }
            )
            if cloud:
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        entry.entry_id != config_entry.entry_id
                        and is_cloud_entry(entry)
                        and self._cloud_credentials(entry)
                        == self._cloud_credentials(config_entry)
                    ):
                        shared_options = dict(entry.options)
                        shared_options[CONF_CLOUD_POLL_INTERVAL] = options[
                            CONF_CLOUD_POLL_INTERVAL
                        ]
                        self.hass.config_entries.async_update_entry(
                            entry, options=shared_options
                        )
            return self.async_create_entry(title="", data=options)

        fields = {}
        if local:
            fields[
                vol.Required(
                    CONF_LOCAL_POLL_INTERVAL,
                    default=str(
                        config_entry.options.get(
                            CONF_LOCAL_POLL_INTERVAL,
                            config_entry.options.get(
                                CONF_POLL_INTERVAL, DEFAULT_LOCAL_POLL_INTERVAL
                            ),
                        )
                    ),
                )
            ] = self._interval_selector()
        if cloud:
            fields[
                vol.Required(
                    CONF_CLOUD_POLL_INTERVAL,
                    default=str(
                        config_entry.options.get(
                            CONF_CLOUD_POLL_INTERVAL,
                            config_entry.options.get(
                                CONF_POLL_INTERVAL, DEFAULT_CLOUD_POLL_INTERVAL
                            ),
                        )
                    ),
                )
            ] = self._interval_selector()
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(fields),
        )

    @staticmethod
    def _interval_selector() -> SelectSelector:
        """Build a polling interval selector."""
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=str(seconds), label=f"{seconds // 60} minutes"
                    )
                    for seconds in POLL_INTERVAL_OPTIONS
                ]
            )
        )

    @staticmethod
    def _cloud_credentials(entry: ConfigEntry) -> tuple[str, str]:
        """Return cloud credentials for legacy or combined entries."""
        source = entry.data.get(CONF_SOURCES, {}).get(ACCESS_MODE_CLOUD, {})
        return (
            str(source.get(CONF_CLOUD_USER_ID, entry.data.get(CONF_CLOUD_USER_ID))),
            str(source.get(CONF_CLOUD_USER_KEY, entry.data.get(CONF_CLOUD_USER_KEY))),
        )
