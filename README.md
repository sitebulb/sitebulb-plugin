# Sitebulb Skills

Official Sitebulb plugin for AI coding agents: five technical-SEO skills that work directly with your Sitebulb Desktop or Cloud audit data. Ask your assistant what to fix first, what changed since the last crawl, produce a client-ready audit document, raise dev tickets, or run your post-release check — all grounded in your real crawl data, never guesswork.

Works in [Claude Code](https://claude.com/claude-code), Codex, Cursor, GitHub Copilot, and other agents that read the open SKILL.md plugin format. Two things are needed everywhere: the plugin (install below) and a connection to the Sitebulb MCP (see [Connecting to Sitebulb](#connecting-to-sitebulb)).

## Installation

### Claude Code

```
/plugin marketplace add sitebulb/sitebulb-plugin
/plugin install sitebulb@sitebulb
```

Then connect the Sitebulb MCP (below).

### Codex

**Codex app:** open **Plugins** from the sidebar, choose **Add plugin marketplace**, enter `sitebulb/sitebulb-plugin` as the source (Git ref `main`), then install **Sitebulb** and restart Codex.

**Codex CLI:**

```bash
codex plugin marketplace add sitebulb/sitebulb-plugin
codex plugin add sitebulb@sitebulb
```

Then connect the Sitebulb MCP (below).

### Cursor

In Cursor Agent chat:

```
/add-plugin sitebulb
```

Or search for "Sitebulb" in the plugin marketplace. Then connect the Sitebulb MCP (below).

### GitHub Copilot

**Copilot CLI** (inside the CLI, or from a shell with the `copilot` binary prefixed by `copilot`):

```
/plugin marketplace add sitebulb/sitebulb-plugin
/plugin install sitebulb@sitebulb
```

**VS Code:** run `Chat: Install Plugin from Source` from the command palette, enter `sitebulb/sitebulb-plugin`, and select **sitebulb**. Then connect the Sitebulb MCP (below).

### Other agents

Any agent that reads Claude-compatible plugin manifests installs this repo directly — for example:

```bash
droid plugin marketplace add https://github.com/sitebulb/sitebulb-plugin && droid plugin install sitebulb@sitebulb
qwen extensions install sitebulb/sitebulb-plugin:sitebulb
grok plugin marketplace add sitebulb/sitebulb-plugin && grok plugin install sitebulb
```

Then connect the Sitebulb MCP (below).

## Connecting to Sitebulb

The skills read your audit data through the Sitebulb MCP. Connect the server for the product you use — this is the only setup step after installing the plugin, and the guide walks you through it for each assistant:

**→ [Sitebulb MCP: Start Here](https://support.sitebulb.com/en/articles/15970977-sitebulb-mcp-start-here)**

The server URL is `https://mcp.sitebulb.com/desktop` for Sitebulb Desktop or `https://mcp.sitebulb.com/cloud` for Sitebulb Cloud, with OAuth sign-in to your Sitebulb account. If a skill runs before the MCP is connected, it will point you at the same guide.

**Requirements:** a Sitebulb Desktop or Sitebulb Cloud licence, at least one finished audit in the project you want to work with, and `python3` available to the agent (the skills bundle small stdlib-only scripts for scoring and document generation). The connection is read-only — skills can read your audits but never trigger crawls.

## The skills

| Skill | What it does | Try |
|---|---|---|
| `sitebulb:what-to-fix-first` | Prioritised triage: the 3–5 issue clusters most worth fixing for your business, impact vs effort | "What should I fix first on this site?" |
| `sitebulb:what-changed` | The change story between your two most recent audits — wins, regressions, watch-list | "What changed since the last crawl?" |
| `sitebulb:technical-seo-audit` | A focused client-facing audit document (.docx working draft, 5–10 issues) shaped by why the audit was commissioned | "Write up the audit for [client]" |
| `sitebulb:dev-handoff` | Dev-ready tickets from audit findings, pushed to your connected PM tool | "Send these to Jira" / "Ticket the quick wins" |
| `sitebulb:release-check` | Your configured post-release watch-list check with thresholds and breach alerts | "Run my Tuesday check" |

Skills trigger automatically when you ask for the matching work — you don't need to invoke them by name.

## Optional integrations

Some features light up when other tools are connected:

- **A PM-tool MCP** (Jira, Linear, Asana, Monday, ClickUp) lets `dev-handoff` create tickets directly. Without one, it produces ready-to-paste markdown ticket bodies.
- **A messaging MCP** (Slack, Teams, …) lets `release-check` post breach alerts to a channel. Without one, alerts appear in chat.
- **Google Analytics / Search Console connected inside Sitebulb** lets `what-to-fix-first` and `technical-seo-audit` weight priorities by real traffic, and gives `what-changed` a search-performance overlay.

## Licence

MIT — see [LICENSE](LICENSE). © Sitebulb Ltd.

## Contributing / maintenance

Skill copies of the shared engine files are generated from [`shared/`](shared/README.md) — edit there and run `python3 scripts/sync_shared.py`. CI enforces sync, runs the scorer test suite, and validates the manifests.
