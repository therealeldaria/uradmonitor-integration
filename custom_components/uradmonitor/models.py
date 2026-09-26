"""Central registry of supported uRADMonitor devices."""

from dataclasses import dataclass
from typing import Final

from .api.local_templates import (
    A3_2016_TEMPLATE,
    A3_2026_TEMPLATE,
    LocalStatusTemplate,
)


@dataclass(frozen=True)
class SupportedDevice:
    """All known identification and setup information for one device family."""

    name: str
    api_types: tuple[str, ...]
    metadata_template: LocalStatusTemplate


# Add a device here when its /j type, model characteristics, and HTML layout
# have been verified. Multiple API types can reuse the same metadata template.
SUPPORTED_DEVICES: Final[tuple[SupportedDevice, ...]] = (
    SupportedDevice(
        name="A3",
        api_types=("8",),
        metadata_template=A3_2016_TEMPLATE,
    ),
    SupportedDevice(
        name="A3",
        api_types=("82",),
        metadata_template=A3_2026_TEMPLATE,
    ),
)


def get_supported_device(device_type: object) -> SupportedDevice | None:
    """Find a supported device family by the type reported by /j."""
    normalized = str(device_type).strip() if device_type is not None else None
    return next(
        (device for device in SUPPORTED_DEVICES if normalized in device.api_types),
        None,
    )


def device_name(device: SupportedDevice, hardware_version: object) -> str:
    """Return the user-facing model name, such as ``A3-104``."""
    hardware = str(hardware_version).strip() if hardware_version else "unknown"
    return f"{device.name}-{hardware}"
