# Sitebulb Skills for Claude Code

Official Sitebulb plugin for [Claude Code](https://claude.com/claude-code): five technical-SEO skills that work directly with your Sitebulb Desktop or Cloud audit data. Ask Claude what to fix first, what changed since the last crawl, produce a client-ready audit document, raise dev tickets, or run your post-release check — all grounded in your real crawl data, never guesswork.

## Installation

```
/plugin marketplace add sitebulb/sitebulb-plugin
/plugin install sitebulb@sitebulb
```

The plugin configures two Sitebulb MCP servers — one for Sitebulb Desktop, one for Sitebulb Cloud. The first time a skill needs your audit data, Claude Code opens a browser window to sign in to your Sitebulb account. Authenticate the server matching the product you use and ignore the other (or disable it under `/mcp`).

**Requirements:** a Sitebulb Desktop or Sitebulb Cloud licence, and at least one finished audit in the project you want to work with. The connection is read-only — skills can read your audits but never trigger crawls.

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
