# Changelog

## 1.0.0 — 2026-11-10

- The `sitebulb` plugin is split into two plugins, `sitebulb-desktop` and `sitebulb-cloud`. `sitebulb` 0.2.0 is the last release of the combined plugin, and `plugins/sitebulb` is removed from the repository and from the Claude, Codex and Cursor marketplace files.
- Each plugin declares one remote MCP server with OAuth sign-in and no headers: `sitebulb-desktop` connects to `https://desktop.mcp.sitebulb.com/mcp` and `sitebulb-cloud` connects to `https://cloud.mcp.sitebulb.com/mcp`. A customer installs the plugin for their product and connects that product in one step.
- Both plugins have the same five skills. `shared/` is the only source: `scripts/sync_shared.py` generates the skills, the licence and the logo of each plugin, and CI fails when a generated file differs or no source produces it.
- Existing users: uninstall `sitebulb`, then install `sitebulb-desktop` or `sitebulb-cloud` for your product (see the README).
- CI runs `claude plugin validate` on each plugin, and the endpoint guard now permits the two plugin URLs as well as the two custom-connector URLs.

## 0.2.0 — 2026-08-11

- All five skills renamed with a `sitebulb-` prefix so they cannot be confused with similarly named skills a user already has installed: `sitebulb-what-to-fix-first`, `sitebulb-what-changed`, `sitebulb-technical-seo-audit`, `sitebulb-dev-handoff`, `sitebulb-release-check`. Skill directories, frontmatter `name` fields, cross-references, `scripts/sync_shared.py` and the README were all updated to match. The CI step that failed on `sitebulb-` prefixed names is replaced by one that fails on un-prefixed ones.

- Added `PRIVACY.md` (no telemetry, local-only scripts, disclosure of the three data paths: AI host, Sitebulb MCP, user-connected integrations) and `SECURITY.md` (private vulnerability reporting via the GitHub Security tab or support.sitebulb.com). The Codex manifest now carries `privacyPolicyURL`.

- Multi-agent support: native plugin manifests for Codex (`.agents/plugins/marketplace.json` at repo root — the manifest Codex's marketplace flow reads, per the canonical `openai/plugins` layout — plus `plugins/sitebulb/.codex-plugin/plugin.json`) and Cursor (`.cursor-plugin/marketplace.json` + `plugins/sitebulb/.cursor-plugin/plugin.json`); GitHub Copilot, Factory Droid, Qwen Code, and Grok CLI install via the existing Claude-compatible manifests. README gains per-host install instructions and a "Connecting to Sitebulb" section.
- Removed the bundled `.mcp.json`: it auto-configured both the Desktop and Cloud MCP servers, but users have one product or the other, so every install surfaced a phantom server with an OAuth prompt the user couldn't complete. Connecting the right server is now a single documented step for every host via the Sitebulb MCP setup guide, which the skills also link when run unconnected.
- `shared-core.md` preflight now handles the no-MCP-connected case explicitly, pointing users at the Sitebulb MCP setup guide (support.sitebulb.com) — the on-ramp for hosts where the plugin cannot auto-configure the MCP servers.
- `technical-seo-audit`: the Word deliverable is now produced by a bundled stdlib-only builder (`scripts/build_docx.py`, with `test_build_docx.py` suite) — JSON document spec in, `.docx` with native anchored review comments out. Removes the dependency on host-specific document tooling so the skill produces identical documents on any agent that can run Python 3.

## 0.1.0 — 2026-07-20

Initial release of the Sitebulb plugin for Claude Code.

- Five skills: `what-to-fix-first`, `what-changed`, `technical-seo-audit`, `dev-handoff`, `release-check`.
- Bundled MCP configuration for Sitebulb Desktop and Sitebulb Cloud (OAuth, read-only).
- Shared engine single-sourced under `shared/` with a sync script and CI drift check.
