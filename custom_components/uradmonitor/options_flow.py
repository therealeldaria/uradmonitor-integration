"""Polling options for uRADMonitor data sources."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    ACCESS_MODE_CLOUD,
    ACCESS_MODE_LOCAL,
    CONF_ACCESS_MODE,
    CONF_CLOUD_POLL_INTERVAL,
    CONF_CLOUD_USER_ID,
    CONF_CLOUD_USER_KEY,
    CONF_LOCAL_POLL_INTERVAL,
    CONF_POLL_INTERVAL,
    CONF_SOURCES,
    DEFAULT_CLOUD_POLL_INTERVAL,
    DEFAULT_LOCAL_POLL_INTERVAL,
    DOMAIN,
    POLL_INTERVAL_OPTIONS,
)
from .coordinator import is_cloud_entry


class UradmonitorOptionsFlow(config_entries.OptionsFlow):
    """Manage independent local and cloud polling intervals."""

    async def async_step_init(
        self, user_input: dict[str, object] | None = None
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
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))

    @staticmethod
    def _interval_selector() -> SelectSelector:
        """Build a polling interval selector."""
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=str(seconds), label=f"{seconds // 60} min")
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
