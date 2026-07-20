# Security Policy

## Supported versions

Security fixes are applied to the latest version on `main`.

## Reporting a vulnerability

Please do not open a public issue for an undisclosed vulnerability. Report it
privately instead, through either channel:

- **GitHub:** use *Report a vulnerability* under this repository's
  [Security tab](https://github.com/sitebulb/sitebulb-plugin/security).
- **Sitebulb support:** contact us via [support.sitebulb.com](https://support.sitebulb.com),
  marking the report as a security issue.

Include a clear description of the issue, reproduction steps or a proof of
concept, an impact assessment (what an attacker can do), and any suggested
mitigation. We will acknowledge receipt as soon as possible and work with you
on validation, remediation, and coordinated disclosure timing.

Issues in the Sitebulb MCP service itself (`mcp.sitebulb.com`) or in Sitebulb
Desktop/Cloud can be reported through the same private channels.

## Scope notes

This repository contains plugin instructions and small local scripts:

- Skill content is markdown read by your AI host; it does not run as a server
  process.
- The bundled Python scripts run locally, use only the standard library, and
  make no network requests.
- Security and privacy behaviour also depends on the host AI tool and any
  external integrations you explicitly connect — see
  [PRIVACY.md](PRIVACY.md) for data-handling details.
