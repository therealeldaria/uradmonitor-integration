# Changelog

All notable changes will be documented here.

## 2026.08.3 - Alpha

- Reissued the combined local/cloud source release after fixing GitHub mirror tag publishing.

## 2026.08.2 - Alpha

- Combine local and cloud sources for the same device using its device ID.
- Prefer local readings while using cloud data for missing sensors or fallback.
- Preserve existing single-source configurations through automatic migration.
- Support independent local and cloud polling intervals for combined devices.
- Mark operational values such as voltage, signal strength, duty cycle, and uptime as diagnostic entities.

## 2026.08.1 - Alpha

- Initial Home Assistant sensor entities for local and cloud uRADMonitor devices.
- Per-device local or cloud configuration with stable device IDs.
- Local runtime polling through `/j`; metadata is collected during setup.
- Shared cloud polling and configurable polling intervals.
- Normalized radiation, pressure, formaldehyde, and sensor metadata values.
- English and Swedish entity translations.
- Local Home Assistant and repository branding icons.
- Tested with uRADMonitor A3 hardware version 104 and software version 124.

This release is experimental and not intended for safety-critical monitoring.
