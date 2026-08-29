"""Data coordinator placeholder for uradmonitor."""

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class UradmonitorCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Coordinate future uradmonitor API updates."""

    async def _async_update_data(self) -> dict[str, object]:
        """Fetch and normalize data once an API client is implemented."""
        return {}
