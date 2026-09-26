# API research

This document is the source-of-truth log for uradmonitor API discovery.

## Current status

The official documentation confirms a local embedded webserver with JSON data and a cloud REST API. Implementation details still need validation against real responses and devices.

## Confirmed documentation

- Local Wi-Fi/Ethernet devices expose an embedded webserver, normally on port `80`.
- Local JSON data is available through the device's JSON endpoint; runtime polling targets `/j`. The HTML status page is queried only during configuration for optional hardware/software metadata because its format varies between devices.
- Cloud base URL: `https://data.uradmonitor.com/api/v1/`.
- Cloud authentication uses `X-User-id` and `X-User-hash` headers.
- `/devices` returns the devices available to the authenticated user.
- `/devices/[ID]` returns the sensors for one device.
- `/devices/[ID]/[sensor]/[startinterval]/[stopinterval]` returns interval data.
- The server specification recommends using `last_<sensor>` fields from `/devices` for normal polling to reduce server load.
- API usage is subject to the published uRADMonitor terms and rate limits.
- The authenticated `/devices` response contains the devices available to the account; a device ID without account access returns an access-denied response in testing.
- Anonymous public-device subscriptions are not currently supported by this integration. The documented REST calls require authentication.

## Research rules

- Prefer official uradmonitor documentation and reproducible observations.
- Record the source and date for every confirmed behavior.
- Distinguish confirmed facts, observed responses, and hypotheses.
- Remove or redact credentials, account identifiers, serial numbers, and network details from committed examples.
- Add sanitized fixtures before implementing parsers.

## Local capture archive

Raw device captures are kept locally under the ignored `.dev/api-captures/`
directory. Name each device folder exactly like its metadata template in
`custom_components/uradmonitor/api/local_templates.py`, and store the captured
`/` response as `local.html` and `/j` response as `local.json`:

```text
.dev/api-captures/
├── A3_2016/
│   ├── local.html
│   └── local.json
└── A3_2026/
    ├── local.html
    ├── local.json
    └── cloud.json
```

The archive is for raw, local research data and is ignored by Git because it
can contain device identifiers, network details, and measurements. Commit only
sanitized, necessary test fixtures under `tests/fixtures/`. The initial A3
captures are observed from local devices: `A3_2016` reports type `8`; `A3_2026`
reports type `82`.

The integration currently polls `/devices`, which returns an account-wide
array, then selects the object whose `id` matches the configured device. The
API also provides a device-specific endpoint at `/devices/<ID>`. Use this
endpoint for a focused cloud capture and save its JSON response beside that
device's local captures as `cloud.json`; for example,
`/devices/82000536` maps to `.dev/api-captures/A3_2026/cloud.json`. Keep in mind
that this endpoint is not the endpoint the integration currently polls, so its
response may differ from the per-device object in `/devices`. Never include the
User ID or User key in the file.

## Open questions

- Which device models expose local JSON APIs?
- Which models and measurements are supported by the cloud API?
- How are devices and measurements identified?
- Which exact response fields and values are returned by each supported model?
- Is local discovery available, and through which protocol?
