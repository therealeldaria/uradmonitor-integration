"""Cloud uRADMonitor API domain."""

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from .errors import UradmonitorApiError

_LOGGER = logging.getLogger(__name__)


class CloudApiClient:
    """Access devices available to an authenticated cloud user."""

    CLOUD_BASE_URL = "https://data.uradmonitor.com/api/v1"
    session: ClientSession
    user_id: str | None
    user_key: str | None

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Fetch devices available to the authenticated cloud user."""
        if not self.user_id or not self.user_key:
            _LOGGER.error("Cloud credentials are missing; cannot list devices")
            raise UradmonitorApiError("Cloud credentials are required")
        _LOGGER.debug("Requesting cloud device list")
        try:
            async with self.session.get(
                f"{self.CLOUD_BASE_URL}/devices",
                headers={"X-User-id": self.user_id, "X-User-hash": self.user_key},
            ) as response:
                _LOGGER.debug("Cloud API returned HTTP status %s", response.status)
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Unable to read cloud device list: %s", err)
            raise UradmonitorApiError("Unable to fetch cloud devices") from err
        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            _LOGGER.error("Cloud API returned an unexpected device-list response")
            raise UradmonitorApiError("Cloud API returned an unexpected response")
        _LOGGER.debug("Cloud API returned %d device(s)", len(data))
        return data
