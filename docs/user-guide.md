# UradMonitor user guide

> This integration is experimental and intended for testing. Do not rely on it for safety-critical monitoring.

## Installation

The planned primary installation method is HACS. Until this project is available through its public GitHub mirror, install it manually by copying or linking `custom_components/uradmonitor/` into the `custom_components/` directory of Home Assistant.

Restart Home Assistant after installing or updating the integration.

## Add a device

In Home Assistant, go to **Settings → Devices & services → Add Integration** and search for **UradMonitor**.

Each physical device is configured as a separate Home Assistant entry. Local and cloud devices can be used together.

Local access requires network access to the device. Cloud access requires an active internet connection to the UradMonitor service.

## Local access

Choose **Local** when Home Assistant can reach the device on the same network.

Enter:

- The device IP address or hostname.
- The optional local API port. The documented default is `80`.

The integration reads JSON data from the device's local JSON endpoint. No API key or cloud credentials are required for local access.

## Cloud access

Choose **Cloud** when the device data should be read through the UradMonitor service.

Enter the **User ID** and **User key** shown in the UradMonitor Dashboard. These values are sent as the `X-User-id` and `X-User-hash` request headers.

After authentication, the integration retrieves the devices available to the account. Select one device to add. Repeat the setup flow to add additional devices.

The exact location and account process for obtaining these values may depend on the UradMonitor service setup.

## Sensors

Available sensor entities depend on the device model and the measurements returned by its API. The supported sensor list will be expanded as models and response fields are verified.

## Security

Treat the User key as a secret. Do not include it in logs, screenshots, issue reports, fixtures, or source control. Redact credentials and device identifiers before sharing diagnostics.

## API references

- [Direct Data Access](https://www.uradmonitor.com/direct-data-access/)
- [uRADMonitor Server API specification](https://www.uradmonitor.com/wp-content/uploads/2025/02/uRADMonitor_server_specs_03_compressed.pdf)
