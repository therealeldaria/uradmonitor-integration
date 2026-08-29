# HACS publication checklist

HACS requires a public GitHub repository. GitLab remains the development, issue, and CI source of truth for this project.

The project must be presented as an unofficial community integration. It must not imply affiliation with, sponsorship by, or endorsement from uRADMonitor or its manufacturer.

Before publication:

- Create the public GitHub mirror.
- Configure `GH_REPOSITORY` and protected `GITHUB_TOKEN` in GitLab CI.
- Verify the integration manifest, `hacs.json`, package layout, and brand asset.
- Verify GitLab issue links remain usable from the GitHub copy.
- Publish a GitHub release for each approved GitLab release tag.
- Validate the GitHub repository with HACS and Home Assistant integration tooling.
- Replace the temporary brand icon when final project branding is available.
