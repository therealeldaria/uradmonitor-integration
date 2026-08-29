"""HTTP clients for the uRADMonitor APIs."""

from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientSession


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
        try:
            async with self.session.get(f"http://{host}:{port}/j") as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UradmonitorApiError("Unable to fetch local device data") from err
        if not isinstance(data, Mapping):
            raise UradmonitorApiError("Local device returned an unexpected response")
        return dict(data)

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Fetch devices available to the authenticated cloud user."""
        if not self.user_id or not self.user_key:
            raise UradmonitorApiError("Cloud credentials are required")
        try:
            async with self.session.get(
                f"{self.CLOUD_BASE_URL}/devices",
                headers={"X-User-id": self.user_id, "X-User-hash": self.user_key},
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UradmonitorApiError("Unable to fetch cloud devices") from err
        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            raise UradmonitorApiError("Cloud API returned an unexpected response")
        return data
