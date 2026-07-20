# Release Check

The post-release ritual: release goes out, the scheduled crawl finishes, you say "run my release check". Compares the latest finished Sitebulb audit against the previous one, evaluates your own watch-list and thresholds (a self-documenting settings block in `SKILL.md` — edit it once, or let the first run fill it in for you), treats changes you name as deliberate as confirmations rather than breaches, then posts a breach alert to a connected messaging or project tool — or gives a brief all-clear.

**Invoke with:** "run my Tuesday check", "release check", "run my watch-list".

**Needs:** a connected Sitebulb Desktop or Cloud MCP with two finished audits (your crawls scheduled in Sitebulb). A messaging MCP (Slack, Teams, …) enables channel alerts; without one, alerts appear in chat. Strictly user-invoked — it cannot schedule itself or trigger crawls.

**Hands off to:** `what-changed` (the full change story), `dev-handoff` (tickets), `what-to-fix-first` (sizing and prioritisation).
