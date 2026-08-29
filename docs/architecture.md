# Architecture

The integration will use one config entry per physical UradMonitor device. Each config entry represents one device, even when cloud setup initially retrieves a list of devices. A config entry selects either a local or cloud transport and owns one coordinator. Local setup stores a host, optional port, and the device ID returned by the JSON endpoint. Cloud setup stores User ID, User key, and the selected device ID. The device ID is the stable Home Assistant identity for both transports, preventing the same physical device from being configured twice through different access modes. The coordinator polls the selected client, normalizes confirmed measurements, and supplies data to sensor entities.

API transports must not leak Home Assistant concerns into parsing. Each client should return normalized models, and entity definitions should consume only the normalized model. Failed polls should use Home Assistant retry behavior and leave entities present but unavailable.

The initial scaffold intentionally has no entities because the API schema is not verified.
