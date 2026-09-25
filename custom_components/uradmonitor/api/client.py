"""Compatibility facade for the local and cloud API domains."""

from aiohttp import ClientSession

from .cloud_client import CloudApiClient
from .errors import UradmonitorApiError
from .local_client import LocalApiClient


class UradmonitorApiClient(LocalApiClient, CloudApiClient):
    """Expose both transport domains through the established client API."""

    def __init__(
        self,
        session: ClientSession,
        *,
        user_id: str | None = None,
        user_key: str | None = None,
    ) -> None:
        """Initialize the shared session and optional cloud credentials."""
        self.session = session
        self.user_id = user_id
        self.user_key = user_key


__all__ = ["UradmonitorApiClient", "UradmonitorApiError"]
