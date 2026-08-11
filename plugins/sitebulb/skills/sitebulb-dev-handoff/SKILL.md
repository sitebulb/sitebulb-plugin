---
name: sitebulb-dev-handoff
description: "Turn Sitebulb audit findings into dev-ready tickets in the connected PM tool (Jira, Linear, Asana, Monday, or ClickUp): one ticket per selected issue — what's wrong, why it matters, the true affected-URL count with labelled sample URLs and a pointer to the full export in the Sitebulb app, a suggested fix with its knowledge-base link, acceptance criteria, severity-mapped priority, and an effort estimate (size and duration) — every draft previewed in chat before anything is created, falling back to markdown ticket bodies when no PM tool is connected. Use when the user wants to raise, create, push, or log tickets/tasks/issues from crawl or audit findings — \"send these to Jira\", \"ticket the quick wins\", \"hand the 404s to the devs\", \"make Linear issues for these\" — not for triggering crawls, since it reads Sitebulb read-only."
---

# Dev Handoff

Turns Sitebulb crawl findings into tickets a developer can act on without asking follow-up questions — each carrying the problem, why it matters, sample and full affected URLs, a suggested fix, acceptance criteria, priority and an effort estimate. Reads Sitebulb data through the Sitebulb MCP and writes through whatever PM-tool MCP is connected.

Before doing anything else, read `references/shared-core.md` — the data-handling rules (noise filtering, sample semantics, score semantics) and its § Tool binding (resolve Sitebulb capabilities to the live tools, plus the preflight) without which the output is wrong, not just worse.

## Preconditions

1. **A Sitebulb MCP is connected.** If not, say so and stop — there is no fallback data source.
2. **The MCP is read-only — it cannot trigger crawls.** If the user asks for "fresh data" or "crawl it first", tell them the latest finished audit is from <date> and that a new crawl must be started in Sitebulb itself; offer to proceed on the existing audit.
3. **A finished audit exists for the target project.** In-progress audits are not usable; name the most recent finished one and its date so the user knows what evidence the tickets rest on.
4. **A PM-tool MCP is connected.** It writes the tickets. If none is, don't dead-end: offer the ticket bodies as formatted markdown the user can paste manually, and note that connecting Jira/Linear/Asana/Monday/ClickUp enables direct creation.

## Framing interview

Ask once, up front, per the rules in `references/shared-core.md` § Invocation framing interview (skip what's already known; challenge vague answers; one round only, then proceed on stated assumptions). Tailored for this skill:

- **Output:** "I'll create tickets in <detected PM tool> — which project/board? Any conventions I should follow: labels, components, assignee, epic? And how many sample URLs in each ticket body (default 10, max 50 — the MCP returns an up-to-50-URL sample per issue)?"
- **Context:** "Is there a sprint deadline, limited dev capacity, or an upcoming release these should align to? That changes how many tickets to raise and how they're prioritised."
- **Role:** "Are these going to your own dev team, or a client's?" Tickets to a client's developers need a more diplomatic, evidence-heavy voice — lead with the data, attribute problems to the issue not the implementation, and avoid anything that reads as blame for past work. Tickets to your own team can be terser.

## Building the tickets

0. **Preflight capabilities** (shared-core § Tool binding), before any data pull and before drafting. *Sitebulb read — core, stop if any can't be matched to a connected tool:* list a project's audits, list the audit's hint categories, list triggered hints per category (the category is a required input, so the category list is load-bearing), and list a hint's affected-URL sample. A missing one almost always means a tool was renamed or removed in a newer Sitebulb release; name the capability you expected, say what you can see instead, and don't build tickets from a source you can't verify — there is no fallback data source. *Sitebulb read — peripheral, note the gap and carry on:* the hint's knowledge-base link (`learnMoreUrl`), GA/GSC traffic data for "why it matters", and the effort map. *PM write — degrade, don't stop:* confirm the connected PM tool's create-issue capability actually resolves, not just that a PM MCP is connected (precondition 4). A renamed write tool is otherwise only discovered after the framing, selection and preview gate; if it doesn't resolve, say so now and switch to the markdown-bodies fallback (precondition 4) rather than running the whole flow to a dead end.
1. **Resolve project and latest finished audit.** Confirm both with the user if there's any ambiguity (similar project names, multiple recent audits).
2. **Gather candidate issues, category-scoped.** List the audit's hint categories, then pull triggered hints per category — apply the shared-core noise filter, sort by severity. Hint rows carry everything the shortlist needs (`affectedUrlsCount`, severity, `warningType`, coverage, indexable split, `urlFilterId`, `learnMoreUrl`) — no per-hint follow-up calls at this stage. If the user said something selective ("the quick wins", "the 404 stuff", "anything critical"), interpret, then show the shortlist — name, severity, `affectedUrlsCount` — and confirm the selection before drafting. Don't ticket an issue the user hasn't seen named. Read **"the quick wins"** as low-effort (S/M, from step 4) among the higher-severity issues — not severity alone; note that the full impact-vs-effort matrix is the What To Fix First skill's job, and offer it if they want true prioritisation.
3. **Read each selected hint's true count and URL sample.** The ticket's affected-URL count is the hint row's `affectedUrlsCount` — never a count of URL-list rows (shared core rule 7). Pull the hint's URL sample (up to 50, unpaginated, one call) via the row's `urlFilterId` — it's on the row, snake_case, ready to pass — and choose the agreed number of sample URLs from it. The row's indexable/not-indexable split, `coverage` and `affectedUrlsChange` are there too: use them in "Why it matters" where they sharpen it (e.g. "23 of 177 indexable; up 8 since the previous audit"), not as padding.
4. **Score effort per issue by calling `scripts/score_effort.py`** — don't hand-compute the join or the arithmetic (`references/effort-scoring.md` is the spec it implements). Pass the selected hints as JSON (each: the row's `url_filter_id` — the canonical, rename-proof join — plus exact `title` and `learn_more_url` as fallbacks, and `affected_urls` set to the hint row's `affectedUrlsCount`) plus the run-level `modifiers`; the script does the title/URL join, banding, modifier netting and floor/cap against the catalogue it reads itself, and returns per hint a `size`, `duration`, `archetype`, `owner` and a ready-to-use `basis` line, plus a run summary. **Modifiers** are passed *only when the relevant context is already known* — volunteered ("we're on WordPress + Yoast" → `cms_self_serve_metadata`; "no dev capacity" → `low_dev_availability`; "solo, no content team" → `solo_no_content_team`; "infra is host-managed" → `host_managed_infra`) or gathered earlier in the session. Don't add framing questions just to size effort; the archetype-plus-band estimate stands on its own. Report the modifiers the summary says it recognised. A hint the script returns as `matched: false` is unmapped — omit its effort block, never guess. If the summary's `drift_warning` is set, surface it: the map may be stale for this Sitebulb version rather than the hints being one-off misses.
5. **Draft one ticket per issue** using the anatomy below. Group only if the user asks (e.g. one ticket per template-level fix).
6. **Preview gate — non-negotiable.** Show every draft in chat (title, body, priority, effort, labels) and wait for explicit confirmation. Creating tickets in someone's PM tool without showing them first is how trust in the whole skill dies. The user may edit, drop, or merge drafts here.
7. **Create the tickets** via the PM MCP, mapping fields per `references/pm-tool-mapping.md`. Apply the `sitebulb` label (or the tool's nearest equivalent) so the user can filter Sitebulb-raised tickets later, and the provenance line.
8. **Point the assignee at the full export.** The MCP returns a sample, never the full list — so no CSV is generated or attached. Every ticket carries a line with the true count and where the full list lives: "Full list (N URLs): export from this hint's Affected URLs view in the Sitebulb app." Don't paste the whole 50-URL sample into a ticket body either — the body carries the agreed sample count, labelled as a sample.
9. **Report results honestly.** List created tickets with links/keys. If some creations failed (auth, permissions, validation), say which succeeded and which failed and why — do not silently retry, which risks duplicates.

### Ticket anatomy

- **Title:** `<Issue name> — <N> URLs affected` (e.g. "Anchored images missing alt text — 91 URLs affected").
- **What's wrong:** two or three sentences, plain language, no SEO jargon a developer wouldn't know.
- **Why it matters:** the consequence (indexability, accessibility, traffic linkage where GA/GSC data exists), not the severity label alone.
- **Sample URLs:** the agreed number (default 10, max 50), drawn from the MCP's up-to-50-URL sample and **labelled as a sample** ("Sample URLs (10 of 177)"), chosen to show variety (different templates/sections) rather than the first ten alphabetically.
- **Full list:** the export pointer line from step 8, carrying the true `affectedUrlsCount`.
- **Suggested resolution:** drawn from the hint's description and knowledge base; always include the hint's `learnMoreUrl` — it is the explanation engine (shared core rule 10).
- **Acceptance criteria:** "A subsequent Sitebulb crawl reports 0 affected URLs for this issue." Concrete and checkable — by the dev team's own QA or their next crawl.
- **Priority:** mapped from hint severity (Critical→highest, High→high, Medium→medium, Low→low). This is the severity-based default; adjust only if the user's stated context (deadline, dev capacity) reorders things, and say so. Priority and effort are separate axes — effort never overrides priority.
- **Effort estimate** (from step 4; omit entirely if the hint is unmapped): a short block, explicitly a planning guide rather than a commitment. Format:

  > **Effort estimate** (planning guide, not a commitment)
  > Size **<S/M/L/XL>**, <duration range> · Fix type: <archetype> · Owner: <owner>
  > Basis: <one line — e.g. "per-URL content work, hard-banded; 253 affected URLs add +2 to a Small base">. <If a modifier was applied or would apply, say so — e.g. "CMS bulk-edit would drop this to ~M."> Team-adjusted sizing and sequencing belong in the What To Fix First output.
- **Provenance** — the last line of the ticket body, plain text (not a code block — it's for the reader, not a parser): *Source: Sitebulb crawl of <project>, <audit date> — <N> URLs affected at time of raise.* It records what evidence the ticket rests on and when, so whoever picks it up knows if the data has since gone stale.

### Worked example

A single assembled ticket (illustrative example.com data, orphaned-URLs hint, 177 URLs — note the count comes from the hint row, the URLs from the 50-URL sample):

```
Title: URL is orphaned and was not found by the crawler — 177 URLs affected
Priority: High    Labels: sitebulb

What's wrong
177 URLs aren't part of the crawlable site architecture — the crawler never
found them via internal links; they surfaced from the XML sitemap, GA or GSC.
Orphans that still return 200 are typically old pages that should be removed,
or live pages that should be linked to and aren't.

Why it matters
Pages with no internal links inherit no link equity and are hard for search
engines to discover and rank. 23 of the 177 are indexable, so search engines
may index pages the site itself never points to. The count is up 8 since the
previous audit (169 → 177), so the set is growing, not legacy-static.

Sample URLs (10 of 177 — a sample, not the full list)
  /blog/2023/spring-product-roundup/
  /products/discontinued/widget-pro/
  /landing/black-friday-2024/
  /help/getting-started/
  /about/old-team-page/
  /events/annual-conference-2023/
  /newsletter/archive/
  /press/media-kit/
  /account/preferences
  /campaigns/summer-launch/

Full list (177 URLs): export from this hint's Affected URLs view in the
Sitebulb app.

Suggested resolution
Triage the 200-responding orphans: remove/redirect stale pages, add internal
links to pages that should be live. Guidance:
https://sitebulb.com/hints/links/url-is-orphaned-and-was-not-found-by-the-crawler/

Acceptance criteria
A subsequent Sitebulb crawl reports 0 affected URLs for this issue.

Effort estimate (planning guide, not a commitment)
Size M, half a day to a day · Fix type: investigation / diagnosis · Owner: SEO lead
Basis: investigation / diagnosis, flat — volume lands on the impact axis, not
effort. Routes to redirect-mapping or linking work once triaged.

Source: Sitebulb crawl of example.com, 26 Jun 2026 — 177 URLs affected at raise.
```

## Failure modes

- **Sitebulb core capability missing (likely a renamed/removed tool):** the preflight (step 0) catches this. Name the capability you expected, note the providing tool may have changed in a newer Sitebulb release, show what's connected instead, and stop — never pull from a substitute tool to keep going. (shared-core § Tool binding.)
- **A query returns empty where the hint row shows a non-zero count:** read it as a probable wrong/renamed `urlFilterId` or reshaped field, not a clean result. Corroborate against the row's `affectedUrlsCount` and surface the discrepancy rather than reporting "no issues". A sample *shorter* than the count is expected (samples cap at 50) — the failure signal is zero rows against a non-zero count. (shared-core rule 7 + § Tool binding.)
- **PM MCP auth/permission error:** report it, point the user at reconnecting the integration, and fall back to markdown ticket bodies so the session still produces value.
- **Partial batch failure:** report created vs failed by name; never blind-retry the whole batch.
- **Field mapping rejection (unknown priority value, missing required field):** consult `references/pm-tool-mapping.md`, retry with the corrected mapping once, then surface the error.
- **Hint not found in the effort map:** the hint may be new in a later Sitebulb release. Omit the effort block for that ticket and note it; never guess an archetype. The ticket is still valid without an estimate. If many hints are unmapped at once, flag possible map staleness rather than treating each as a one-off (step 4).

## Reference

- `scripts/score_effort.py` — deterministic effort scorer: title/URL join + banding + modifiers + floor/cap, returning size/duration/owner/basis per hint and a run summary with a drift signal. Call it in step 4; don't hand-compute. (`scripts/test_score_effort.py` is its test suite.)
- `references/shared-core.md` — Sitebulb data-handling rules v2 (sample semantics, category-scoped hint access), the § Tool binding capability map + preflight, and the framing-interview protocol. Read before any data pull.
- `references/effort-scoring.md` — fix archetypes, volume bands, modifiers, durations: the spec `score_effort.py` implements. Read before scoring effort (step 4).
- `references/hint-map.csv` — the classified catalogue (358 hints, `urlFilterId`-keyed): archetype, owner, volume sensitivity, base size, lane, tier, section weight. Read by the script, not into context.
- `references/pm-tool-mapping.md` — per-tool field mapping, label equivalents, and the runtime-discovery rule.
