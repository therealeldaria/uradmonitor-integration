"""HTTP clients for the uRADMonitor APIs."""

import logging
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class UradmonitorApiError(Exception):
    """Raised when an uRADMonitor API request fails."""


class UradmonitorApiClient:
    """Client for local and cloud uRADMonitor data access."""

    CLOUD_BASE_URL = "https://data.uradmonitor.com/api/v1"

    def __init__(
        self,
        session: ClientSession,
        *,
        user_id: str | None = None,
        user_key: str | None = None,
    ) -> None:
        """Initialize the client."""
        self.session = session
        self.user_id = user_id
        self.user_key = user_key

    async def async_get_local_data(self, host: str, port: int = 80) -> dict[str, Any]:
        """Fetch the local JSON endpoint."""
        url = f"http://{host}:{port}/j"
        _LOGGER.debug("Requesting local device data from %s", url)
        try:
            async with self.session.get(url) as response:
                _LOGGER.debug("Local device returned HTTP status %s", response.status)
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning(
                "Local device request failed for %s:%s: %s", host, port, err
            )
            raise UradmonitorApiError("Unable to fetch local device data") from err
        if not isinstance(data, Mapping):
            _LOGGER.error("Local device returned a non-object JSON response")
            raise UradmonitorApiError("Local device returned an unexpected response")
        fields = sorted(data)
        if isinstance(data.get("data"), Mapping):
            fields = [*fields, "data." + ", data.".join(sorted(data["data"]))]
        _LOGGER.debug("Local device data received with fields: %s", fields)
        return dict(data)

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Fetch devices available to the authenticated cloud user."""
        if not self.user_id or not self.user_key:
            _LOGGER.error("Cloud request cannot be made without User ID and User key")
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
            _LOGGER.warning("Cloud device request failed: %s", err)
            raise UradmonitorApiError("Unable to fetch cloud devices") from err
        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            _LOGGER.error("Cloud API returned an unexpected device-list response")
            raise UradmonitorApiError("Cloud API returned an unexpected response")
        _LOGGER.debug("Cloud API returned %d device(s)", len(data))
        return data
