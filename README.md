# uradmonitor Home Assistant Integration

> Early development: experimental and not production-ready.

> **GitHub mirror:** This repository is a read-only release mirror. All development, issues, and CI are managed in the canonical [GitLab repository](https://gitlab.com/therealeldaria/uradmonitor-integration). Please report issues and submit contributions there. GitHub releases are published from approved GitLab tags.

This project is a Python Home Assistant custom integration for uRADMonitor environmental monitoring devices. It presents supported measurements as Home Assistant sensor entities for dashboards, automations, and history.

This is an unofficial community integration. It is not affiliated with, sponsored by, or endorsed by uRADMonitor or its manufacturer.

## Current capabilities

- Multiple independently configured uradmonitor devices.
- One Home Assistant config entry per physical device.
- Per-device selection of local API or cloud API access.
- Stable identity based on the API-provided device ID.
- Normalized sensor values and Home Assistant metadata, including local/cloud unit conversion.
- Retry and availability handling when a device or service is temporarily unavailable.
- Shared cloud polling for devices using the same account.

The local API uses the device's embedded web server. Metadata is read from the HTML status page once during configuration; runtime readings are read from `/j`. The cloud API uses the User ID and User key from the UradMonitor Dashboard and lists devices available to that account. The device ID returned by either API is used as the stable Home Assistant identity. Anonymous public-device subscriptions are not supported.

Local access requires network access to the device. Cloud access requires an active internet connection. Home Assistant classifies this integration as local polling because it supports direct communication with local devices.

## Configuration

Setup is UI-only through Home Assistant’s config flow. Each device gets its own entry and can choose local or cloud access independently. Local setup uses the device host and optional port (default `80`). Cloud setup uses the User ID and User key from the UradMonitor Dashboard; after authentication, one available device is selected. Repeat setup to add more devices. Credentials are stored per device entry and must never appear in logs, fixtures, issues, or source control.

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

Local polling defaults to every 5 minutes. Cloud polling defaults to every 15 minutes and can be changed in the integration options. Cloud entries using the same account share the selected interval. These defaults are intentionally conservative because uRADMonitor publishes hourly and daily API limits.

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

## HACS and hosting

Development, issues, and CI are hosted in GitLab. The public GitHub repository is the release mirror used for HACS distribution. Install the integration through HACS from the GitHub mirror; for development, use the canonical GitLab repository.

Approved GitLab release tags are mirrored to GitHub by GitLab CI, which also creates the corresponding GitHub release.

## Status and roadmap

1. Expand verified model mappings and sensor coverage.
2. Add diagnostics and reauthentication/reconfiguration.
3. Validate additional hardware versions and API response variants.
4. Publish stable releases after broader testing.

Calendar-versioned releases will remain explicitly experimental/alpha until the configuration model, entities, and API support are stable.

## License

Licensed under the GNU Affero General Public License, version 3 or later. See [LICENSE](LICENSE).
