"""HTTP clients for the uRADMonitor APIs."""

import asyncio
import json
import logging
import socket
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientSession

from .local_templates import LocalStatusTemplate

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
            page, status = await asyncio.to_thread(
                self._fetch_local_page, host, port, "/j"
            )
            _LOGGER.debug("Local device returned HTTP status %s", status)
            data = json.loads(page)
        except (ClientError, TimeoutError, OSError, ValueError) as err:
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

    async def async_get_local_metadata(
        self,
        host: str,
        port: int = 80,
        template: LocalStatusTemplate | None = None,
    ) -> dict[str, str]:
        """Fetch hardware and software metadata from the local status page."""
        return await self._async_get_local_status(
            host, port, metadata_only=True, template=template
        )

    async def async_get_local_status_data(
        self, host: str, port: int = 80
    ) -> dict[str, Any]:
        """Reject HTML sensor polling; local sensors come from /j."""
        raise UradmonitorApiError("Local sensor data is available from /j only")

    async def _async_get_local_status(
        self,
        host: str,
        port: int,
        *,
        metadata_only: bool,
        template: LocalStatusTemplate | None = None,
    ) -> dict[str, Any]:
        """Fetch and parse the single-request local status page."""
        url = f"http://{host}:{port}/"
        _LOGGER.debug("Requesting local device status from %s", url)
        try:
            page, status = await asyncio.to_thread(
                self._fetch_local_page, host, port, "/"
            )
            _LOGGER.debug("Local device status returned HTTP status %s", status)
        except (TimeoutError, OSError, ValueError) as err:
            _LOGGER.warning(
                "Local device status request failed for %s:%s: %s", host, port, err
            )
            raise UradmonitorApiError("Unable to fetch local device status") from err

        if template is None:
            raise UradmonitorApiError("No local status metadata template selected")
        if not metadata_only:
            raise UradmonitorApiError("Local status data is metadata-only")
        metadata = template.parse_metadata(page)
        _LOGGER.debug(
            "Local device metadata received with fields: %s", sorted(metadata)
        )
        return metadata

    @staticmethod
    def _fetch_local_page(host: str, port: int, path: str) -> tuple[str, str]:
        """Fetch a local endpoint using a blocking HTTP/1.0 socket."""
        request = (
            f"GET {path} HTTP/1.0\r\nHost: {host}\r\n"
            "Connection: close\r\n"
            "User-Agent: Home Assistant\r\n"
            "Accept: */*\r\n\r\n"
        ).encode()
        with socket.create_connection((host, port), timeout=5) as connection:
            connection.sendall(request)
            response = bytearray()
            while b"\r\n\r\n" not in response:
                response.extend(connection.recv(4096))
            header_bytes, body = bytes(response).split(b"\r\n\r\n", 1)
            headers = header_bytes.decode("latin-1").split("\r\n")
            status = headers[0].split(" ", 2)
            if len(status) < 2 or not status[1].startswith("2"):
                raise UradmonitorApiError("Local device returned an HTTP error")
            content_length_header = next(
                (
                    line
                    for line in headers[1:]
                    if line.lower().startswith("content-length:")
                ),
                None,
            )
            content_length = (
                int(content_length_header.split(":", 1)[1].strip())
                if content_length_header
                else None
            )
            while content_length is None or len(body) < content_length:
                try:
                    chunk = connection.recv(4096)
                except TimeoutError:
                    # Some device generations send a complete body but keep the
                    # socket open or advertise an inaccurate Content-Length.
                    # Return what we have; JSON/HTML parsing will reject a truly
                    # incomplete response.
                    if body:
                        break
                    raise
                if not chunk:
                    break
                body += chunk
        if not body:
            raise TimeoutError("Local device returned an empty response")
        text = body[:content_length] if content_length else body
        return text.decode("utf-8", errors="replace"), status[1]

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
