# Changelog

All notable changes will be documented here.

## 2026.09.1 - Beta

- Add local A3 type `82` support using the `A3_2026` metadata template.
- Identify local devices from the JSON `/j` type and keep sensor polling on JSON; HTML scraping is limited to static metadata.
- Add confirmed Zeroconf discovery, retry failed availability checks, and avoid automatically adding discovered devices.
- Offer discovered-device setup as Merge, Local Only, or Cloud Only.
- Archive sanitized local and cloud API examples for A3_2016 and A3_2026.
- Move the project status from Alpha to Beta; model coverage remains experimental.

## 2026.08.4 - Alpha

- Keep local and cloud readings as separate Home Assistant devices and entities.
- Use source-specific identifiers while retaining the physical device ID for matching and display.

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
