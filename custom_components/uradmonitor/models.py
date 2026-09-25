"""Central registry of supported uRADMonitor devices."""

from dataclasses import dataclass
from typing import Final

from .api.local_templates import LEGACY_A3_TEMPLATE, LocalStatusTemplate


@dataclass(frozen=True)
class SupportedDevice:
    """All known identification and setup information for one device family."""

    name: str
    model: str
    api_types: tuple[str, ...]
    detector_hardware: tuple[tuple[str, str], ...]
    metadata_template: LocalStatusTemplate


# Add a device here when its /j type, model characteristics, and HTML layout
# have been verified. Multiple API types can reuse the same metadata template.
SUPPORTED_DEVICES: Final[tuple[SupportedDevice, ...]] = (
    SupportedDevice(
        name="A3",
        model="Model A3",
        api_types=("8",),
        detector_hardware=(("SI29BG", "104"), ("SI29BG", "110")),
        metadata_template=LEGACY_A3_TEMPLATE,
    ),
    SupportedDevice(
        name="A",
        model="Model A",
        api_types=(),
        detector_hardware=(("SBM20", "109"),),
        metadata_template=LEGACY_A3_TEMPLATE,
    ),
)


def get_supported_device(device_type: object) -> SupportedDevice | None:
    """Find a supported device family by the type reported by /j."""
    normalized = str(device_type).strip() if device_type is not None else None
    return next(
        (device for device in SUPPORTED_DEVICES if normalized in device.api_types),
        None,
    )


def get_model(detector: object, hardware_version: object) -> str:
    """Return the registered model for detector and hardware characteristics."""
    key = (str(detector), str(hardware_version))
    return next(
        (
            device.model
            for device in SUPPORTED_DEVICES
            if key in device.detector_hardware
        ),
        "Unknown",
    )


def device_name(device: SupportedDevice, hardware_version: object) -> str:
    """Return the user-facing model name, such as ``A3-104``."""
    hardware = str(hardware_version).strip() if hardware_version else "unknown"
    return f"{device.name}-{hardware}"
