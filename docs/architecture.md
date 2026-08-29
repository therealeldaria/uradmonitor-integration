# Architecture

The integration uses one config entry per physical UradMonitor device. Each entry can contain a local transport, a cloud transport, or both. Local setup stores a host, optional port, and metadata discovered during configuration; runtime readings come from the device's `/j` JSON endpoint. Cloud setup stores User ID, User key, and the selected device ID. The device ID is the stable Home Assistant identity for both transports. Source coordinators poll independently, and a combined coordinator merges normalized readings with local values taking precedence over cloud values.

During setup, the integration registers the physical device in Home Assistant's device registry using the stable UradMonitor device ID. This allows the device to appear in the Devices view even before its sensor entities are implemented.

API transports must not leak Home Assistant concerns into parsing. Each client should return normalized models, and entity definitions should consume only the normalized model. Failed polls should use Home Assistant retry behavior and leave entities present but unavailable.

Sensor entities are created from the normalized fields returned by the active source coordinators. The entity set is the union observed during initial setup, so source-specific measurements remain available when local and cloud data are combined.
