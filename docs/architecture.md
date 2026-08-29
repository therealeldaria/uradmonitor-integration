# Architecture

The integration will use one config entry per physical uradmonitor device. A config entry selects either a local or cloud transport and owns one coordinator. The coordinator polls the selected client, normalizes confirmed measurements, and supplies data to sensor entities.

API transports must not leak Home Assistant concerns into parsing. Each client should return normalized models, and entity definitions should consume only the normalized model. Failed polls should use Home Assistant retry behavior and leave entities present but unavailable.

The initial scaffold intentionally has no entities because the API schema is not verified.
