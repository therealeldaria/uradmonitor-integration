# Architecture

The integration uses one config entry per physical UradMonitor device. Each entry can contain a local transport, a cloud transport, or both. Local setup first reads `/j`; its `type` selects a device definition containing a user-facing device name and a reusable HTML metadata template. The template reads static hardware/software metadata from `/` only; it never supplies sensor readings or device identity. Runtime local readings come exclusively from `/j`, while static HTML metadata is refreshed once when the entry starts. Cloud setup stores User ID, User key, and the selected device ID. The device ID matches sources to the same physical unit, while each transport receives a source-specific Home Assistant device identifier and its own entities. Source coordinators poll independently; readings are intentionally not merged.

During setup, the integration registers the physical device in Home Assistant's device registry using the stable UradMonitor device ID. This allows the device to appear in the Devices view even before its sensor entities are implemented.

API transports must not leak Home Assistant concerns into parsing. Each client should return normalized models, and entity definitions should consume only the normalized model. Failed polls should use Home Assistant retry behavior and leave entities present but unavailable.

Sensor entities are created from the normalized fields returned by each source coordinator. Source-specific measurements remain visible on the device that supplied them, even when both transports are configured for the same physical unit.
