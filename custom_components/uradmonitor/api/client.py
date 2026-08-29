"""HTTP clients for the uRADMonitor APIs."""

import asyncio
import json
import logging
import re
import socket
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
        self, host: str, port: int = 80
    ) -> dict[str, str]:
        """Fetch hardware and software metadata from the local status page."""
        url = f"http://{host}:{port}/"
        _LOGGER.debug("Requesting local device metadata from %s", url)
        try:
            page, status = await asyncio.to_thread(
                self._fetch_local_page, host, port, "/"
            )
            _LOGGER.debug("Local device metadata returned HTTP status %s", status)
        except (
            TimeoutError,
            OSError,
            ValueError,
        ) as err:
            _LOGGER.warning(
                "Local device metadata request failed for %s:%s: %s", host, port, err
            )
            raise UradmonitorApiError("Unable to fetch local device metadata") from err
        id_match = re.search(r"<b>uRADMonitor\s+(?P<id>[^<\s]+)</b>", page)
        match = re.search(
            r"type:(?P<type>\S+)\s+hw:(?P<hw>\S+)\s+sw:(?P<sw>\S+)\s+(?P<detector>[^<\s]+)",
            page,
        )
        if not match:
            _LOGGER.debug("Local device metadata page did not contain known metadata")
            return {}
        metadata = {
            "device_id": id_match.group("id") if id_match else None,
            "device_type": match.group("type"),
            "hardware_version": match.group("hw"),
            "software_version": match.group("sw"),
            "detector": match.group("detector"),
        }
        metadata = {key: value for key, value in metadata.items() if value is not None}
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
            content_length = next(
                int(line.split(":", 1)[1].strip())
                for line in headers[1:]
                if line.lower().startswith("content-length:")
            )
            while len(body) < content_length:
                body += connection.recv(4096)
        return body[:content_length].decode("utf-8", errors="replace"), status[1]

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
