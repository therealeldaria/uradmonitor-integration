"""Known uRADMonitor model mappings."""

from typing import Final

# Confirmed from the development cloud account and local device metadata.
# Keep this table keyed by hardware characteristics so it can also identify
# devices that are not in the original account.
MODEL_MAPPINGS: Final[dict[tuple[str, str], str]] = {
    ("SBM20", "109"): "Model A",
    ("SI29BG", "104"): "Model A3",
    ("SI29BG", "110"): "Model A3",
}


def get_model(detector: object, hardware_version: object) -> str:
    """Return a known model or ``Unknown`` for an unmapped device."""
    key = (str(detector), str(hardware_version))
    return MODEL_MAPPINGS.get(key, "Unknown")
