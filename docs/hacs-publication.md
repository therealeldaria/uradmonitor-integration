# HACS publication checklist

HACS requires a public GitHub repository. GitLab remains the development and CI source of truth; GitHub is the public release mirror and community issue tracker.

## Installing before default-list inclusion

Until the repository is accepted into the HACS default list, users must add the GitHub mirror as a custom repository:

1. Open HACS and select the three-dot menu.
2. Choose **Custom repositories**.
3. Add `https://github.com/therealeldaria/uradmonitor-integration`.
4. Select **Integration**.
5. Add and download the repository.
6. Restart Home Assistant, then add **UradMonitor** from **Settings → Devices & services**.

The GitLab repository must not be used as the HACS repository. GitLab is the canonical development repository; GitHub is the public release mirror that HACS reads.

The project must be presented as an unofficial community integration. It must not imply affiliation with, sponsorship by, or endorsement from uRADMonitor or its manufacturer.

Before publication:

- Create the public GitHub mirror.
- Configure `GH_REPOSITORY` and protected `GITHUB_TOKEN` in GitLab CI.
- Verify the integration manifest, `hacs.json`, package layout, and `custom_components/uradmonitor/brand/` assets.
- Keep user-facing issue links pointed at GitHub Issues.
- Publish a GitHub release for each approved GitLab release tag.
- Validate the GitHub repository with HACS and Home Assistant integration tooling.
- Confirm the original brand icon and hDPI icon are included in the published repository.

HACS's current guidance for custom repositories is documented at <https://www.hacs.xyz/docs/faq/custom_repositories/>. To become a default HACS repository, the project must continue to meet HACS validation and Home Assistant integration requirements, pass the HACS and Hassfest GitHub Actions, and have a full GitHub release before submitting a pull request to `hacs/default`.
