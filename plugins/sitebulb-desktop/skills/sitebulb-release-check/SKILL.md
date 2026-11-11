---
name: sitebulb-release-check
description: "Run the user's configured post-release watch-list check on a Sitebulb project: compare the latest finished audit against the previous one, evaluate each watched item against the thresholds in this file's settings block (project, watch-list, thresholds and alert channel live there — the first run asks setup once and hands the filled block back to paste in), treat changes the user names as deliberate as confirmations rather than breaches, then post a breach alert via a connected messaging or project tool — in chat when none is connected — or give a two-to-four-sentence all-clear. Strictly user-invoked; it cannot schedule itself or trigger crawls. Use for \"run my Tuesday check\", \"release check\", \"run my watch-list\", \"run my release check on [project name]\", or the user's own named check ritual. Not for open-ended \"what changed\" or \"did the release break anything\" change-story conversations — that is the sitebulb-what-changed skill; this is the configured ritual with thresholds and alerts."
---

# Release Check

The Tuesday ritual: release goes out Monday, the scheduled crawl finishes Tuesday, the user says "run my Tuesday check". The job is narrow by design — compare the latest finished audit against the previous one, evaluate the user's own watch-list and thresholds, and either raise a breach alert or confirm all-clear briefly. Everything is configured once in the settings block below; the only question a routine run asks is "what went out in the release?". This skill is not a change-story explorer (that is the sitebulb-what-changed skill) and never sizes fixes (sitebulb-what-to-fix-first) or raises tickets (sitebulb-dev-handoff) — it detects, alerts, and hands off.

It is strictly user-invoked. The assistant cannot schedule this check or trigger crawls — the Sitebulb connection is read-only. Never claim otherwise; the ritual works because the user's crawl is already scheduled in Sitebulb.

Before doing anything else, read `references/shared-core.md` — the data-handling rules (noise filtering, delta and split semantics, sample semantics) and its § Tool binding (resolve Sitebulb capabilities to the live tools, plus the preflight) without which the check is wrong, not just quiet.

## Your settings — edit this block

<!-- ═════════════ RELEASE CHECK SETTINGS — YOURS TO EDIT ═════════════
This block is the skill's memory. Fill it in once — or let the first run
ask the setup questions and hand you this block back filled in, ready to
paste over this section — and every future check runs with no setup, just
"what went out?". Write watch items in your own words; the assistant maps
them to the audit data at run time. Thresholds compare the latest finished
audit against the one before it.
-->

**Project:** *not set — the first run asks which Sitebulb project this check watches, then hands this line back filled in.*

**Watch-list and thresholds** — alert when any of these moves past its limit since the previous audit:

- Pages newly blocked from search (noindex, robots.txt, canonical mistakes): any increase of 10+ URLs or 25%
- Broken internal links and new 404s: 10+ more than the previous audit
- Internal links pointing at redirects: 25+ more
- Any Critical issue that is new, or grows by 10+ URLs or 10%
- Overall audit score: a drop of 5+ points — a score that disappears to zero means that area wasn't measured this audit, never a collapse

**Alert channel:** *not set — if a messaging or project tool is connected, the first breach asks where to post and this line records it; with none connected, alerts appear in chat.*

<!-- ═════════════ END SETTINGS ═════════════ -->

## Preconditions

1. **A Sitebulb MCP is connected** (Desktop and Cloud are tool-for-tool identical). If not, say so and stop — there is no fallback data source.
2. **Two finished audits exist to compare.** Take the previous-audit flag from the change-list or per-category hint tools. If the flag is genuinely false, there is nothing to compare: say so, and recommend keeping the scheduled crawls running so next week's check has a baseline. Do not fabricate a comparison or fall back to a current-state read — that is the sitebulb-what-changed skill's job, offered as a handoff, not performed here.
3. **The latest audit must postdate the release.** State the audit's date next to the release the user describes. If the crawl ran *before* the release went out, the check cannot see it yet: say the latest finished audit is from <date>, that a fresh crawl must be run in Sitebulb itself, and offer either to stop or to run the check anyway clearly labelled as pre-release data.

## First run vs. the ritual

**First run** — the Project line above is unfilled: ask which Sitebulb project this check watches (offer the project list if unclear), and read the watch-list back in one breath for confirmation or edits ("watching indexability, broken links, redirect links, new Criticals, and the audit score — keep, drop, or add anything?"). One round, then run. After the run, hand back the entire settings block with the answers filled in and tell the user to paste it over the block in this file so next Tuesday is zero-setup. Within a conversation, never re-ask anything answered.

**Every run** — one question, always: **"What went out in the release?"** The answer is load-bearing: it separates deliberate change from regression. A change the user names as intended (a URL restructure, a removed section, a new template) is never alerted as a breach — it appears as one line confirming the data matches what they shipped. If the user says "nothing" or doesn't know, evaluate everything at face value and say so.

## The check

0. **Preflight capabilities** (shared-core § Tool binding). *Core — stop if unmatched:* list a project's audits; list changed hints vs the previous audit; list an audit's hint categories and triggered hints per category (the per-row previous counts corroborate the change list). *Peripheral — note the gap and carry on:* the per-changed-hint URL sample; report snapshots (only the score watch item needs them); the knowledge-base link. Everything this check needs comes from the audit pair.
1. **Resolve the project and the audit pair.** Name both dates in the output ("comparing 10 Jul against 26 Jun") so the user knows the window, and check the window actually contains the release (precondition 3).
2. **Scope sanity-check before believing any delta** (shared-core rule 3). If the crawled-URL total shifted materially between the pair, raw deltas mislead — evaluate thresholds on proportions, and lead the output with the scope change, which may itself be the release's footprint.
3. **Pull the deltas from two sources, cross-read:** the changed-hints list (noise-filtered per rule 1: drop severity-none and crawl-report rows; the change sign read per rule 5 — negative is an improvement on issue hints) and the per-category triggered-hint rows, whose previous-audit counts carry the same deltas. Where the two disagree, surface the discrepancy rather than picking either reading.
4. **Map the watch-list to the data.** Each watch item is plain language; find the hint movements that genuinely embody it (an "internal links pointing at redirects" item covers the internal-redirect hints, not every redirect-adjacent row). Judgment, not keyword matching — when a mapping is genuinely uncertain, say which hints were counted against the item. The score item reads the audit overview (`audit_report_summary`): one call carries the site score current-and-previous *and* the priority-band counts with deltas, so the "new or growing Critical" watch item reads off the same response — remembering a zero means not measured.
5. **Gather the at-a-glance panel's six numbers**, each with its change since the previous audit (current and previous values read from the same response): **Audit score** from the audit overview (`audit_report_summary`); **SEO score** from the SEO snapshot (`audit_report_seo`); **Performance score** from the performance report in the report catalogue; **Indexable** and **Not indexable** page counts from the indexability report's statistics; **Broken pages** from the broken-internal-URLs hint row's current and previous counts. A zero score or an absent report means that area wasn't measured this audit — the panel shows "not measured", never a 0 or a collapse. The audit overview already carries the audit score and crawl scope, so the panel's remaining figures cost at most three extra report reads (SEO, performance, indexability) beyond the calls the check makes anyway.
6. **Evaluate.** For each watch item: breached, moved-but-under-threshold, or quiet. Then apply the release answer: movements the user named as deliberate are removed from the breach set and confirmed in one line. Movements *not* on the watch-list are out of scope for alerting — at most one closing sentence ("outside your watch-list, nothing else moved materially" or "…the full story is a sitebulb-what-changed run away"). Don't manufacture drama; a threshold not crossed is not a near-miss to dramatise.
7. **One of two outputs — both open with the at-a-glance panel:**

   **The panel** — two banks of three, scores over site metrics, each figure with its change since the previous audit: row one **Audit score · SEO score · Performance score**; row two **Indexable pages · Not indexable pages · Broken pages**. Changes are shown as up/down arrows with the number (green/red only where the direction is genuinely good/bad — a score up is good, broken pages up is bad, indexable counts are neutral facts unless a watch item says otherwise). Render it with whatever inline visual capability the assistant supports; where none is available — and always inside an alert posted to a channel — the same panel as aligned plain text, one line per bank. The content is identical either way (portability: no dependency on assistant-specific surfaces).

   **All-clear** — genuinely brief: two to four sentences. The window, the verdict, any deliberate change confirmed, done. No cards, no per-item inventory, no caveats parade. The ritual's value is that a clean Tuesday costs the user ten seconds.

   **Breach alert** — compact and self-sufficient, per breached item:
   - What breached, in plain language, with the numbers: the true affected count off the hint row with its change and the window ("broken on-page anchor links went from 52 to 122, past your limit of 25 more").
   - The likely tie to the release where the "what went out" answer plausibly explains it — as a lead worth checking, never a verdict.
   - **Up to 5 sample URLs where the sample genuinely helps**, fetched via the changed hint's URL sample. The sample cannot isolate which URLs are newly affected — its states describe crawl presence, not when the hint started applying — so label it "Sample (5 of 122 currently affected)", never "newly affected". Disappeared-URL movements carry no URL identities: report the count only, with no sample section.
   - The export pointer — "Full list (N URLs): export from this hint's Affected URLs view in the Sitebulb app" — and the hint's knowledge-base Learn More link.
   - A suggested next step: fix-and-recrawl, "want these as dev tickets?" (the sitebulb-dev-handoff skill), "want the full change story?" (the sitebulb-what-changed skill), or "want it sized and prioritised?" (the sitebulb-what-to-fix-first skill).

   **Voice — the machinery never appears in either output, and the alert is user-facing even when it lands in a channel the user's colleagues read.** Tool names, response field names, flag names, lost-and-found terminology, "noise-filtered", "severity: none" — all internal working. Translate every reading into plain consequence, in the vocabulary of the settings block the user wrote.

8. **Post the alert.** Resolve a connected tool by capability, not name: anything that can post a message to a channel or person (Slack, Teams, and the like are examples) or create an item in a project tracker (Jira, Linear, Asana, and the like) qualifies — read the connected tools' actual schemas before mapping, the same discipline as shared-core § Tool binding. On the first breach, show the alert in chat and confirm the destination before posting; record it on the settings block's Alert channel line (and include it in the paste-back). Thereafter, post to the recorded channel and show what was posted in chat. With no such tool connected, the in-chat alert is the alert — one clause, no ceremony. If a post fails, deliver the alert in chat and say the posting failed; the alert itself must never be lost to a delivery error.

## Failure modes

- **No previous audit** (per the change-list/hint tools): nothing to compare — say so and stop, recommending scheduled crawls; offer sitebulb-what-changed's baseline read as a handoff if the user wants a current-state look.
- **Latest audit predates the release:** the check can't see the release yet (precondition 3) — never present pre-release data as a post-release verdict.
- **Sitebulb core capability missing** (likely a renamed/removed tool): the preflight catches it — name the capability expected, show what's connected instead, stop; never substitute another tool's data.
- **A URL sample returns empty where the hint row shows a non-zero count:** a probable renamed identifier, not a clean result — corroborate against the row's count and surface the discrepancy (shorter-than-count samples are expected; zero rows against a non-zero count is the failure signal).
- **Material scope shift between the pair:** lead with it and evaluate proportionally (step 2).
- **The user asks to schedule the check or trigger a crawl:** the assistant can do neither — the check runs when the user invokes it, and crawls are scheduled in Sitebulb itself. Say so plainly and offer to run on the latest finished audit.
- **Alert posting fails:** in-chat delivery, with the failure named (step 7).

## Reference

- `references/shared-core.md` — Sitebulb data-handling rules, § Tool binding capability map + preflight. Read before any data pull.
