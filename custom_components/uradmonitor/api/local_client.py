"""Local uRADMonitor API domain."""

import asyncio
import json
import logging
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientSession

from .errors import UradmonitorApiError
from .http import fetch_local_page
from .local_templates import LocalStatusTemplate

_LOGGER = logging.getLogger(__name__)


class LocalApiClient:
    """Access local JSON readings and static HTML metadata."""

    session: ClientSession

    async def async_get_local_data(self, host: str, port: int = 80) -> dict[str, Any]:
        """Fetch the local JSON endpoint used for runtime readings."""
        url = f"http://{host}:{port}/j"
        _LOGGER.debug("Requesting local device data from %s", url)
        try:
            page, status = await asyncio.to_thread(fetch_local_page, host, port, "/j")
            _LOGGER.debug("Local device returned HTTP status %s", status)
            data = json.loads(page)
        except (ClientError, TimeoutError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Unable to read local device data from %s:%s: %s",
                host,
                port,
                err,
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

    async def async_get_local_metadata(
        self,
        host: str,
        port: int = 80,
        template: LocalStatusTemplate | None = None,
    ) -> dict[str, str]:
        """Fetch static metadata from the local HTML status page."""
        url = f"http://{host}:{port}/"
        _LOGGER.debug("Requesting local device metadata from %s", url)
        try:
            page, status = await asyncio.to_thread(fetch_local_page, host, port, "/")
            _LOGGER.debug("Local device metadata returned HTTP status %s", status)
        except (TimeoutError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Unable to read optional metadata from local device %s:%s: %s",
                host,
                port,
                err,
            )
            raise UradmonitorApiError("Unable to fetch local device status") from err
        if template is None:
            raise UradmonitorApiError("No local status metadata template selected")
        metadata = template.parse_metadata(page)
        _LOGGER.debug(
            "Local device metadata received with fields: %s", sorted(metadata)
        )
        return metadata

    async def async_get_local_status_data(
        self, host: str, port: int = 80
    ) -> dict[str, Any]:
        """Reject HTML sensor polling; local sensors come from /j."""
        raise UradmonitorApiError("Local sensor data is available from /j only")
