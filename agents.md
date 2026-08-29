# AI contributor guide

## Project

`uradmonitor` is an early-development Home Assistant custom integration for uradmonitor environmental monitoring devices. It is intended for HACS distribution, with GitLab as the canonical development and issue-tracking project and a future public GitHub mirror for HACS.

The implementation language is Python. Follow current Home Assistant APIs and asynchronous I/O conventions.

## Design decisions

- Use one Home Assistant config entry per physical device.
- Configure each device through the UI config flow; do not add YAML configuration.
- Each device independently selects the local API or cloud API.
- Store credentials per entry and never log or commit secrets.
- Use a stable serial number or API-provided unique identifier for identity. Never use an IP address as identity.
- Expose only a documented, normalized set of supported measurements.
- Use a coordinator for polling, retries, availability, and shared data.
- Keep API clients inside this integration until a reusable library is justified.
- Treat API behavior as unknown until confirmed by official documentation, sanitized responses, or reproducible device tests.

## Repository layout

- `custom_components/uradmonitor/`: runtime integration code.
- `custom_components/uradmonitor/api/`: local/cloud transports and normalized models.
- `tests/`: Home Assistant fixture tests and pure client tests.
- `tests/fixtures/`: sanitized, non-secret API responses.
- `docs/`: API research, architecture, and HACS notes.
- `.gitlab-ci.yml`: merge-request and `main` quality gates.
- `compose.dev.yml` and `.dev/homeassistant/`: isolated manual Home Assistant test instance.

## Development rules

- Prefer small, reviewable changes with tests.
- Use type annotations, clear names, and Home Assistant helpers.
- Never block the event loop.
- Keep user-facing text in `strings.json` and translations.
- Redact tokens, passwords, email addresses, and device identifiers in diagnostics and logs.
- Preserve config-entry migration paths when stored data changes.
- Never make live-network tests mandatory.
- Update `README.md`, `CHANGELOG.md`, or `docs/` when behavior or setup changes.

## Required checks

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Merge requests must pass Ruff, pytest, JSON/manifest validation, and Home Assistant checks in GitLab CI. The default branch is `main`.

Manual Home Assistant testing uses the Podman instance described in `docs/development-homeassistant.md`. It uses host networking and port `8123`; never use the production Home Assistant configuration for development.

## Release and hosting

GitLab is the source of truth. Releases use calendar versioning and identify experimental/alpha status in the release title and changelog. An approved GitLab release triggers protected CI automation that mirrors the tag and publishes a GitHub release for future HACS consumption. GitLab remains the issue tracker.

Do not assume the GitLab repository itself is installable through HACS. HACS distribution requires a public GitHub repository.

## Unknown APIs

Start API work by recording sources and observations in `docs/api-research.md`. Separate confirmed facts, observed responses, and hypotheses. Add a fixture before implementing a parser. If a device model or measurement is not confirmed, leave it out of the supported entity set.
