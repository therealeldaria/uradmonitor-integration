# Home Assistant development instance

The repository includes a separate Podman-based Home Assistant instance for manual integration testing. It uses the standard Home Assistant port `8123`; the production Home Assistant instance is on separate hardware.

## Start

From the repository root:

```bash
podman compose -f compose.dev.yml up -d
```

If the installed Compose provider tries to use a Docker socket instead of the
local Podman engine, start the same service directly with Podman:

```bash
podman run -d --name uradmonitor-homeassistant-dev \
  --restart unless-stopped \
  --network host \
  --env TZ=Europe/Stockholm \
  --volume "$PWD/.dev/homeassistant:/config:Z" \
  --volume "$PWD/custom_components/uradmonitor:/config/custom_components/uradmonitor:Z" \
  ghcr.io/home-assistant/home-assistant:stable
```

Open <http://localhost:8123> and complete the initial Home Assistant onboarding. The development configuration is stored under `.dev/homeassistant/` and is ignored by Git.

The repository integration is mounted directly into the container, so source changes are available after restarting Home Assistant:

```bash
podman compose -f compose.dev.yml restart homeassistant
```

## Logs and stop

```bash
podman compose -f compose.dev.yml logs -f homeassistant
podman compose -f compose.dev down
```

The container uses host networking so local uradmonitor APIs and discovery can be tested. Do not place production secrets or production configuration in `.dev/homeassistant/`.

For a directly started container, use `podman logs -f
uradmonitor-homeassistant-dev` and `podman rm -f
uradmonitor-homeassistant-dev` instead of the compose commands.
