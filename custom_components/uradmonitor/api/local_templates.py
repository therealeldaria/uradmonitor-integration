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


@dataclass(frozen=True)
class LocalDeviceDefinition:
    """Definition selected by the device type reported by ``/j``."""

    name: str
    metadata_template: LocalStatusTemplate


def _parse_legacy_a3_metadata(page: str) -> Metadata:
    """Parse metadata from the compact status page used by the original A3."""
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


LEGACY_A3_TEMPLATE = LocalStatusTemplate(
    "legacy_a3_metadata", _parse_legacy_a3_metadata
)


# This is the device-type translation table. Multiple type values may point to
# the same definition and therefore reuse the same HTML metadata template.
LOCAL_DEVICE_TYPES: dict[str, LocalDeviceDefinition] = {
    "8": LocalDeviceDefinition("A3", LEGACY_A3_TEMPLATE),
}


def get_local_device_definition(device_type: Any) -> LocalDeviceDefinition | None:
    """Return the device definition for a type reported by /j."""
    if device_type is None:
        return None
    return LOCAL_DEVICE_TYPES.get(str(device_type).strip())


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


def device_name(definition: LocalDeviceDefinition, hardware_version: Any) -> str:
    """Return the user-facing model name, such as ``A3-104``."""
    hardware = str(hardware_version).strip() if hardware_version else "unknown"
    return f"{definition.name}-{hardware}"
