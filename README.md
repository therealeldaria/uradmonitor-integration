# uradmonitor Home Assistant Integration

> Early development: experimental and not production-ready.

This project is a Python Home Assistant custom integration for uRADMonitor environmental monitoring devices. It presents supported measurements as Home Assistant sensor entities for dashboards, automations, and history.

This is an unofficial community integration. It is not affiliated with, sponsored by, or endorsed by uRADMonitor or its manufacturer.

## Current capabilities

- Multiple independently configured uradmonitor devices.
- One Home Assistant config entry per physical device.
- Per-device local API and/or cloud API access with separate Home Assistant devices.
- Stable identity based on the API-provided device ID.
- Normalized sensor values and Home Assistant metadata, including local/cloud unit conversion.
- Retry and availability handling when a device or service is temporarily unavailable.
- Shared cloud polling for devices using the same account.

The local API uses the device's embedded web server. Metadata is read from the HTML status page once during configuration; runtime readings are read from `/j`. The cloud API uses the User ID and User key from the UradMonitor Dashboard and lists devices available to that account. If both sources are configured for the same physical device, Home Assistant shows separate `(Local)` and `(Cloud)` devices because the values may use different compensation and aggregation. Anonymous public-device subscriptions are not supported.

Local access requires network access to the device. Cloud access requires an active internet connection. Home Assistant classifies this integration as local polling because it supports direct communication with local devices.

## Configuration

Setup is UI-only through Home Assistant’s config flow. Each physical device gets its own entry and can use local access, cloud access, or both. Add the second source normally; the integration matches it automatically using the device ID and creates a separate source device. Local setup uses the device host and optional port (default `80`). Cloud setup uses the User ID and User key from the UradMonitor Dashboard; after authentication, one available device is selected. Repeat setup to add more devices. Credentials are stored per device entry and must never appear in logs, fixtures, issues, or source control.

Cloud setup can only add devices returned for the authenticated account. This includes owned devices and any devices for which uRADMonitor grants the account global access. A device ID alone is not sufficient for anonymous access.

The integration has been tested with a uRADMonitor A3 using hardware version `104` and software version `124`.

## Development

Prerequisites: Python supported by the current Home Assistant development dependency and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The project uses Ruff, pytest with Home Assistant test utilities, and GitLab CI for merge-request and `main` checks.

The integration writes structured logs under `custom_components.uradmonitor`. Enable debug logging temporarily when investigating local or cloud connection problems; credentials are redacted and never logged.

Local polling defaults to every 5 minutes. Cloud polling defaults to every 15 minutes and can be changed independently in the integration options. Cloud sources using the same account share the selected interval. These defaults are intentionally conservative because uRADMonitor publishes hourly and daily API limits.

For manual testing, start the isolated Podman development instance with `podman compose -f compose.dev.yml up -d`. It uses Home Assistant's standard port, `8123`, and is documented in [docs/development-homeassistant.md](docs/development-homeassistant.md).

## Repository structure

```text
custom_components/uradmonitor/  Home Assistant integration
tests/                           Unit and Home Assistant fixture tests
docs/                            Research and architecture notes
brand/                           Repository brand icon
icon.svg                         Source vector icon
icon.png                         Repository icon
```

## Install with HACS

The repository is public on GitHub, but it is not yet part of the HACS default repository list. Add it as a custom repository:

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu in the upper-right corner.
3. Select **Custom repositories**.
4. Enter `https://github.com/therealeldaria/uradmonitor-integration`.
5. Select **Integration** as the repository type.
6. Click **Add**, open the repository in HACS, and choose **Download**.
7. Restart Home Assistant.

You can also use this [My Home Assistant link](https://my.home-assistant.io/redirect/hacs_repository/?owner=therealeldaria&repository=uradmonitor-integration&category=integration) to open the repository in HACS. The link may still require the repository to be added as a custom repository.

After installation, add **UradMonitor** from **Settings → Devices & services → Add Integration**. HACS will use the GitHub releases for updates.

Development, issues, and CI are hosted in GitLab. The public GitHub repository is the release mirror used for HACS distribution. For development, use the canonical GitLab repository.

Approved GitLab release tags are mirrored to GitHub by GitLab CI, which also creates the corresponding GitHub release.

## Status and roadmap

1. Expand verified model mappings and sensor coverage.
2. Add diagnostics and reauthentication/reconfiguration.
3. Validate additional hardware versions and API response variants.
4. Publish stable releases after broader testing.

Calendar-versioned releases will remain explicitly experimental/alpha until the configuration model, entities, and API support are stable.

## License

Licensed under the GNU Affero General Public License, version 3 or later. See [LICENSE](LICENSE).
