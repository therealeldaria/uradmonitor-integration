"""Device definitions and metadata templates for local uRADMonitor pages."""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..const import (
    CONF_DETECTOR,
    CONF_DEVICE_TYPE,
    CONF_HARDWARE_VERSION,
    CONF_SOFTWARE_VERSION,
)

Metadata = dict[str, str]


@dataclass(frozen=True)
class LocalStatusTemplate:
    """Parser for static metadata on a device's HTML status page."""

    name: str
    parse_metadata: Callable[[str], Metadata]


def _parse_a3_2016_metadata(page: str) -> Metadata:
    """Parse metadata from the compact A3 status page used since 2016."""
    metadata_match = re.search(
        r"(?:type:\S+\s+)?hw:(?P<hw>\S+)\s+sw:(?P<sw>\S+)\s+"
        r"(?P<detector>[^<\s]+)",
        page,
    )
    if not metadata_match:
        return {}
    return {
        CONF_HARDWARE_VERSION: metadata_match.group("hw"),
        CONF_SOFTWARE_VERSION: metadata_match.group("sw"),
        CONF_DETECTOR: metadata_match.group("detector"),
    }


A3_2016_TEMPLATE = LocalStatusTemplate(
    "a3_2016_metadata", _parse_a3_2016_metadata
)


def _parse_a3_2026_metadata(page: str) -> Metadata:
    """Parse metadata from the newer A3 status page.

    The newer page puts the hardware and software versions in its heading and
    does not expose the detector chip. Sensor values in the rest of the page
    are intentionally ignored.
    """
    metadata_match = re.search(
        r"uRADMonitor\s+A3\s+[^<\s]+\s+-\s*"
        r"HW:\s*(?P<hw>[^\s<]+)\s+SW:\s*(?P<sw>[^\s<]+)",
        page,
        re.IGNORECASE,
    )
    if not metadata_match:
        return {}
    return {
        CONF_HARDWARE_VERSION: metadata_match.group("hw"),
        CONF_SOFTWARE_VERSION: metadata_match.group("sw"),
        CONF_DETECTOR: "Unknown",
    }


A3_2026_TEMPLATE = LocalStatusTemplate(
    "a3_2026_metadata", _parse_a3_2026_metadata
)


def local_json_metadata(data: Mapping[str, Any]) -> Metadata:
    """Extract static device metadata from a local JSON response."""
    payload = data.get("data", data)
    if not isinstance(payload, Mapping):
        return {}
    aliases = {
        CONF_DEVICE_TYPE: ("type", "device_type"),
        CONF_HARDWARE_VERSION: ("hardware_version", "hw", "versionhw"),
        CONF_SOFTWARE_VERSION: ("software_version", "sw", "versionsw"),
        CONF_DETECTOR: ("detector",),
    }
    metadata: Metadata = {}
    for key, names in aliases.items():
        value = next(
            (payload[name] for name in names if payload.get(name) is not None),
            None,
        )
        if value is not None:
            metadata[key] = str(value)
    return metadata
