"""HTTP transport for embedded local uRADMonitor servers."""

import socket

from .errors import UradmonitorApiError


def fetch_local_page(host: str, port: int, path: str) -> tuple[str, str]:
    """Fetch a local endpoint using a tolerant HTTP/1.0 socket client."""
    request = (
        f"GET {path} HTTP/1.0\r\nHost: {host}\r\n"
        "Connection: close\r\nUser-Agent: Home Assistant\r\n"
        "Accept: */*\r\n\r\n"
    ).encode()
    with socket.create_connection((host, port), timeout=5) as connection:
        connection.sendall(request)
        response = bytearray()
        while b"\r\n\r\n" not in response:
            chunk = connection.recv(4096)
            if not chunk:
                raise ConnectionError("Local device closed before sending headers")
            response.extend(chunk)
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
