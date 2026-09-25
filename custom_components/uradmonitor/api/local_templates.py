"""Templates for parsing uRADMonitor local status pages."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Metadata = dict[str, str]
Values = dict[str, float]


@dataclass(frozen=True)
class LocalStatusTemplate:
    """HTML parser selected from the device type reported by ``/j``."""

    name: str
    parse: Callable[[str], tuple[Metadata, Values]]


def _parse_legacy_a3(page: str) -> tuple[Metadata, Values]:
    """Parse the compact status page used by the original A3 generation."""
    id_match = re.search(r"<b>uRADMonitor\s+(?P<id>[^<\s]+)</b>", page)
    metadata_match = re.search(
        r"type:(?P<type>\S+)\s+hw:(?P<hw>\S+)\s+sw:(?P<sw>\S+)\s+"
        r"(?P<detector>[^<\s]+)",
        page,
    )
    metadata = {
        "device_id": id_match.group("id") if id_match else None,
        "device_type": metadata_match.group("type") if metadata_match else None,
        "hardware_version": metadata_match.group("hw") if metadata_match else None,
        "software_version": metadata_match.group("sw") if metadata_match else None,
        "detector": metadata_match.group("detector") if metadata_match else None,
    }
    metadata = {key: value for key, value in metadata.items() if value is not None}

    values: Values = {}
    for key, pattern in {
        "cpm": r"radiation:(?P<value>[\d.]+)CPM",
        "temperature": r"temperature:(?P<value>[\d.]+)C",
        "pressure": r"pressure:(?P<value>[\d.]+)Pa",
        "humidity": r"humidty:(?P<value>[\d.]+)RH",
        "voc": r"VOC:(?P<value>[\d.]+)",
        "ch2o": r"CH2O:(?P<value>[\d.]+)ppm",
        "pm25": r"PM2\.5:(?P<value>[\d.]+)ug/m\^3",
        "co2": r"CO2:(?P<value>[\d.]+)ppm",
        "voltage": r"voltage:(?P<value>[\d.]+)V",
        "duty": r"duty:(?P<value>[\d.]+)%",
        "uptime": r"uptime:(?P<value>[\d.]+)s",
    }.items():
        if match := re.search(pattern, page):
            values[key] = float(match.group("value"))
    return metadata, values


# Keep this table as the single place where new local device types are added.
# The type values are the values returned by the device's /j JSON endpoint.
LOCAL_STATUS_TEMPLATES: dict[str, LocalStatusTemplate] = {
    "8": LocalStatusTemplate("legacy_a3", _parse_legacy_a3),
}


def get_local_status_template(device_type: Any) -> LocalStatusTemplate | None:
    """Return the HTML template for a device type reported by /j."""
    if device_type is None:
        return None
    return LOCAL_STATUS_TEMPLATES.get(str(device_type).strip())
