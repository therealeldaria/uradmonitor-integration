# UradMonitor user guide

> This integration is experimental and intended for testing. Do not rely on it for safety-critical monitoring.

This is an unofficial community integration. It is not affiliated with, sponsored by, or endorsed by uRADMonitor or its manufacturer.

## Installation

The primary installation method is HACS through the public GitHub release mirror. For development or before the mirror is available, install it manually by copying or linking `custom_components/uradmonitor/` into the `custom_components/` directory of Home Assistant.

Restart Home Assistant after installing or updating the integration.

## Add a device

In Home Assistant, go to **Settings → Devices & services → Add Integration** and search for **UradMonitor**.

Each physical device is configured as a separate Home Assistant entry. A device may use local access, cloud access, or both. To add both sources, add the second source normally and select the same device; the integration matches sources by device ID but keeps separate Local and Cloud Home Assistant devices.

Local and cloud entities are deliberately not merged because their values can use different compensation and aggregation. Polling remains independent: local polling defaults to five minutes and cloud polling defaults to fifteen minutes.

Local access requires network access to the device. Cloud access requires an active internet connection to the UradMonitor service.

## Local access

Choose **Local** when Home Assistant can reach the device on the same network.

Enter:

- The device IP address or hostname.
- The optional local API port. The documented default is `80`.

The integration reads runtime data from the device's `/j` JSON endpoint. The HTML status page is read once during setup for optional hardware metadata. No API key or cloud credentials are required for local access.

## Cloud access

Choose **Cloud** when the device data should be read through the UradMonitor service.

Enter the **User ID** and **User key** shown in the UradMonitor Dashboard. These values are sent as the `X-User-id` and `X-User-hash` request headers.

After authentication, the integration retrieves the devices available to the account. Select one device to add. Repeat the setup flow to add additional devices.

Only devices returned for the authenticated account can be added. This includes devices owned by the account and devices where uRADMonitor has granted the account global access. Anonymous public device IDs are not supported.

The exact location and account process for obtaining these values may depend on the UradMonitor service setup. Cloud polling defaults to every 15 minutes and is shared by entries using the same account. Local polling defaults to every 5 minutes.

## Sensors

Available sensor entities depend on the device model and the measurements returned by its API. The supported sensor list will be expanded as models and response fields are verified.

## Security

Treat the User key as a secret. Do not include it in logs, screenshots, issue reports, fixtures, or source control. Redact credentials and device identifiers before sharing diagnostics.

## Logging

The integration logs setup, API requests, response validation, and connection failures under `custom_components.uradmonitor`. API keys and User keys are never written to the log.

For detailed troubleshooting, add this to Home Assistant's `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.uradmonitor: debug
```

Set the logger back to `info` after troubleshooting to avoid unnecessary log volume.

## API references

- [Direct Data Access](https://www.uradmonitor.com/direct-data-access/)
- [uRADMonitor Server API specification](https://www.uradmonitor.com/wp-content/uploads/2025/02/uRADMonitor_server_specs_03_compressed.pdf)
