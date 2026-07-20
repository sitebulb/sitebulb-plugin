# Changelog

## Unreleased

- Multi-agent support: native plugin manifests for Codex (`.agents/plugins/marketplace.json` at repo root — the manifest Codex's marketplace flow reads, per the canonical `openai/plugins` layout — plus `plugins/sitebulb/.codex-plugin/plugin.json`, which points `mcpServers` at the bundled `.mcp.json` so Codex auto-configures the Sitebulb MCP on install) and Cursor (`.cursor-plugin/marketplace.json` + `plugins/sitebulb/.cursor-plugin/plugin.json`); GitHub Copilot, Factory Droid, Qwen Code, and Grok CLI install via the existing Claude-compatible manifests. README gains per-host install instructions and a "Connecting to Sitebulb" section.
- `shared-core.md` preflight now handles the no-MCP-connected case explicitly, pointing users at the Sitebulb MCP setup guide (support.sitebulb.com) — the on-ramp for hosts where the plugin cannot auto-configure the MCP servers.
- `technical-seo-audit`: the Word deliverable is now produced by a bundled stdlib-only builder (`scripts/build_docx.py`, with `test_build_docx.py` suite) — JSON document spec in, `.docx` with native anchored review comments out. Removes the dependency on host-specific document tooling so the skill produces identical documents on any agent that can run Python 3.

## 0.1.0 — 2026-07-20

Initial release of the Sitebulb plugin for Claude Code.

- Five skills: `what-to-fix-first`, `what-changed`, `technical-seo-audit`, `dev-handoff`, `release-check`.
- Bundled MCP configuration for Sitebulb Desktop and Sitebulb Cloud (OAuth, read-only).
- Shared engine single-sourced under `shared/` with a sync script and CI drift check.
