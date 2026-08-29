"""Data coordinator placeholder for uradmonitor."""

import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class UradmonitorCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate future uradmonitor API updates."""

    async def _async_update_data(self) -> dict[str, object]:
        """Fetch and normalize data once an API client is implemented."""
        _LOGGER.debug("Updating UradMonitor coordinator data")
        return {}
