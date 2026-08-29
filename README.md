# uradmonitor Home Assistant Integration

> Early development: experimental and not production-ready.

This project is a Python Home Assistant custom integration for uradmonitor environmental monitoring devices. It will present supported measurements as Home Assistant sensor entities for dashboards, automations, and history.

## Planned capabilities

- Multiple independently configured uradmonitor devices.
- One Home Assistant config entry per physical device.
- Per-device selection of local API or cloud API access.
- Stable identity based on a device serial number or API-provided unique ID.
- A documented, normalized set of sensor entities with Home Assistant metadata.
- Retry and availability handling when a device or service is temporarily unavailable.
- Optional local discovery when the protocol is confirmed.

Exact device models, measurements, endpoints, authentication, polling limits, and API response shapes are intentionally not promised yet. They will be added as confirmed during API research.

## Configuration

The intended setup is UI-only through Home Assistant’s config flow. Each device gets its own entry and can choose local or cloud access independently. Credentials are stored per device entry and must never appear in logs, fixtures, issues, or source control.

## Development

Prerequisites: Python supported by the current Home Assistant development dependency and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The project uses Ruff, pytest with Home Assistant test utilities, and GitLab CI for merge-request and `main` checks.

For manual testing, start the isolated Podman development instance with `podman compose -f compose.dev.yml up -d`. It uses Home Assistant's standard port, `8123`, and is documented in [docs/development-homeassistant.md](docs/development-homeassistant.md).

## Repository structure

```text
custom_components/uradmonitor/  Home Assistant integration
tests/                           Unit and Home Assistant fixture tests
docs/                            Research and architecture notes
brand/                           Temporary HACS/Home Assistant icon
```

## HACS and hosting

Development, issues, and CI are hosted in GitLab. HACS currently requires a public GitHub repository, so the planned distribution model is a GitLab source repository with an automated public GitHub release mirror. Until that mirror exists, install the integration only through a local custom-component checkout.

The integration layout and metadata are being prepared for HACS compatibility. A future release pipeline will mirror approved GitLab tags and GitHub releases so HACS can discover updates.

## Status and roadmap

1. Research official local and cloud APIs and supported device models.
2. Implement normalized models and mocked API clients.
3. Add config-flow validation and per-device local/cloud setup.
4. Implement coordinator, device registry entries, and initial sensor entities.
5. Add diagnostics, reauthentication/reconfiguration, and optional discovery.
6. Validate with Home Assistant tooling and prepare the GitHub HACS mirror.

Calendar-versioned releases will remain explicitly experimental/alpha until the configuration model, entities, and API support are stable.

## License

Licensed under the GNU Affero General Public License, version 3 or later. See [LICENSE](LICENSE).
