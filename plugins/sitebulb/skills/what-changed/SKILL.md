---
name: what-changed
description: "Tell the change story between a Sitebulb project's two most recent audits — wins first, then regressions, then a watch-list, each with what it means and whether it needs action — reframed for the business's situation, with a Google Analytics/Search Console overlay where connected, evidence cards showing per-hint deltas, and an optional self-contained HTML dashboard. Use for \"what changed since last crawl\", \"monthly check\", \"progress since last month\", \"did we get better or worse\", \"did the release/deploy break anything\", \"did the migration cause this\", or prepping a client update — including a \"client meeting in 20 minutes\" short version. Not for full-site triage (what-to-fix-first), raising dev tickets (dev-handoff), client audit documents (technical-seo-audit), or configured watch-list/threshold alerting (release-check)."
---

# What Changed

The job is to help the user understand what changed since the last crawl, and what to do about it. Consultation-first: establish context, deliver a conversational read of the deltas, stay in the conversation. The read compares the latest finished audit against the previous one only — multi-audit trending is out of scope by design.

Before doing anything else, read `references/shared-core.md` — the data-handling rules (noise filtering, sample semantics, delta and split semantics) and its § Tool binding (resolve Sitebulb capabilities to the live tools, plus the preflight) without which the change story is wrong, not just worse. Then read `references/context-emphasis.md` — the reframe rules that decide what leads.

## Preconditions

1. **A Sitebulb MCP is connected** (Desktop and Cloud are tool-for-tool identical). If not, say so and stop — there is no fallback data source.
2. **The MCP is read-only — it cannot trigger crawls.** If the user asks for fresh data, tell them the latest finished audit is from <date> and a new crawl must be started in Sitebulb itself; offer to proceed on the existing pair.
3. **A finished audit exists for the target project.** Name it and its date. If `hasPreviousAudit` is false there is no change story: say so plainly, offer a current-state read of the latest audit instead (framed as the baseline the next comparison will run against), and recommend scheduled crawls so next month has a story. Never fake a delta.

## The context interview

Ask once, up front, before any data pull — one round only, per the shared-core interview rules (skip what's already known or evident; challenge non-answers; then proceed on stated assumptions). Light-touch, conversationally:

- **What happened this period:** "anything happen this month — releases, content pushes, seasonality?" This is the load-bearing question: it separates intended change from regression. A user who arrived via a release/deploy phrasing ("did Tuesday's release break anything?") has already answered it — don't re-ask; treat the release as the stated event and the comparison window's lead hypothesis.
- **Business type and situation** — only if not already known from the conversation or a prior run: the type list and situation list in `references/context-emphasis.md`. The two situations that most reshape this skill's read are **routine check** (deltas first, brief, don't manufacture drama) and **traffic decline** (every delta framed as "could this explain the drop?"; opportunity-class changes demoted).

**Refusal default:** if the user skips or doesn't know, proceed with no reframe and say that's what's happening. Never stall on an unanswered interview.

## Building the read

0. **Preflight capabilities** (shared-core § Tool binding). *Core — stop if unmatched:* list a project's audits; list changed hints vs the previous audit (`audit_lostfound_hint_list`); list an audit's hint categories and triggered hints per category (the per-row previous-audit counts corroborate the deltas). *Peripheral — note the gap and carry on:* the per-changed-hint URL sample (`audit_lostfound_url_list`); the report catalogue and aggregate report snapshots (the GA/GSC overlay); `learnMoreUrl`.

   **Never walk URLs for traffic data** — each single-URL column read returns the full column set (~12k tokens); a per-URL sweep exhausts context long before it finishes. The overlay in step 4 uses aggregate reports only.

1. **Resolve project and the audit pair.** Confirm the project if ambiguous. Identify the latest finished audit and its predecessor; state both dates in the read ("comparing 10 Jul against 26 Jun") so the user knows the window. Record whether GA/GSC data is attached (the report catalogue shows it).

2. **Scope sanity-check before believing any delta** (shared-core rule 3). The one-call audit overview (`audit_report_summary`) gives the fastest orientation: a single response carries both audits' crawl-scope totals, the site score with its change, and the priority-band deltas — read the crawled-URL totals from it first. If the scope shifted materially, raw count deltas mislead — compare ratios or lead with the scope change itself ("the crawl grew from 1,000 to 4,000 URLs, so every raw count moved; here's what changed in proportion"). A migration or settings change often *is* the story. This overview orients and sizes scope; it does not replace the per-hint change list in step 3.

3. **Pull the change story from two sources, cross-read:**
   - `audit_lostfound_hint_list`, noise-filtered per shared-core rule 1 (drop `severity: none` and `crawl_report` rows). Read `netChange` per rule 5 — negative is an improvement on issue hints.
   - The per-category triggered-hint lists (`audit_hint_category_list` → `audit_hint_list`), whose rows carry `affectedUrlsChange` and previous-audit counts. Deltas read straight off the row; where the two sources disagree, say so rather than picking the flattering one.
   - Classify each surviving change: **improvement** (issue shrank or resolved), **regression** (issue grew or appeared), or **watch** (moved, but small, ambiguous, or plausibly explained by the stated events). A hint absent from the new audit may mean its category wasn't measured, not that the issue is gone (rule 2) — corroborate before celebrating.
   - **Missing-URL changes are count-only**: lost & found `state=missing` rows carry no URL identities. Report the count and what it implies; never attempt to list which URLs went missing.

4. **GA/GSC overlay — from the audit's own aggregate keyword and traffic reports only.** If attached, fetch the relevant aggregate report snapshots via the report catalogue and read the period's search picture from them: clicks/impressions movement, top queries and pages gaining or losing. Tie it to the change story where the data genuinely links ("the templates that regressed are the ones losing clicks"), and say when it doesn't. Zero organic visits between non-zero snapshots is a data gap, never a collapse (rule 4). If GA/GSC isn't attached, skip the overlay, say the read would sharpen with the connection, and never treat missing data as zero traffic.

5. **Reframe per `references/context-emphasis.md`.** The situation picks what leads and the narrative arc; nothing here changes what the data says. **Routine check:** deltas first, brief, escalate only genuine movement — don't manufacture drama from noise-level wobble. **Traffic decline:** the read becomes hypothesis-testing — lead with indexability regressions, noindex/canonical/robots accidents, redirect breakage; frame each as "could this explain the drop?"; demote opportunity-class changes definitively; be honest when nothing in the crawl could explain it (algorithmic and competitive causes are outside Sitebulb's sight). **Migration/redesign just happened:** ask what changed deliberately so intended changes aren't reported as regressions. Demotions are honest and explicit, in the user's terms.

6. **Present the read — analysis first, then evidence cards.**

   **Voice — the machinery never appears in the output.** The people reading this did not author the skill. Lost-and-found terminology, `netChange`, `crawl_report`, "noise-filtered", "severity none", tool names, field names, flag names — all internal working. The read says "two regressions, one improvement since 26 June", never the plumbing. Translate every internal reading into plain consequence.

   **The analysis** — wins first, then regressions, then the watch-list. Per item:
   - **What it means** — the consequence in this business's context, tied to the stated events where they plausibly explain it ("this appeared the week of your release — worth checking whether the new template shipped without canonicals").
   - **Whether it needs action** — a plain call: fix it, watch it, or celebrate it and move on. This skill's job is what changed and whether it needs action, **not sizing the work**. If an effort estimate genuinely helps ("is this a big job?" asked directly), it comes from `scripts/score_effort.py` — never ad hoc — and is always paired with what the work actually is; a bare duration reads as inflated or arbitrary. Otherwise leave sizing to the what-to-fix-first skill and say so.

     ```bash
     echo '{"hints":[{"url_filter_id":"broken_internal_urls","title":"Broken internal URLs",
                      "affected_urls":43}]}' | python3 scripts/score_effort.py
     ```

   **The evidence cards** — after the analysis, one card per featured change, mirroring the Sitebulb hint layout so users recognise it from the app:
   - Header: severity pill + issue-type tag + the hint title.
   - Stat row: **URLs** (the true `affectedUrlsCount`, with the change vs previous audit as an up/down arrow and the previous count), **Percentage** (coverage), **Indexable** and **Not Indexable** with changes — omit the indexable pair where the hint type doesn't carry the split (shared-core rule 9: the 0/0 form is never "none indexable"; duplicate-content sets are wholly indexable by design — use that in the analysis rather than showing zeros).
   - One or two plain-language sentences on what the hint means.
   - **Up to 10 sample URLs** for regressed or fixed hints, via `audit_lostfound_url_list` on the change row, labelled as a sample with the true count. The sample cannot isolate the newly-affected subset (its states describe crawl presence, not when the hint started applying), so label it honestly — "Sample URLs (10 of 122 currently affected)", never "newly affected".
   - **Missing-URL changes get a count-only card** — no sample section at all, rather than an empty one.
   - Footer: the export pointer ("Full list (N URLs): export from this hint's Affected URLs view in the Sitebulb app") and the Learn More link (`learnMoreUrl`). The Sitebulb app is the only export route to name.

   Render the cards with whatever inline visual/rich output the assistant supports; where none is available, the same card as clean markdown — identical content either way.

7. **Two depths.** The default is the **monthly client version** — the full analysis and cards above. When the user signals time pressure ("client meeting in 20 minutes", "give me the short version"), produce the **20-minutes version**: the headline sentence (net position vs last crawl), the one or two changes that need a decision or a mention in the meeting, and one line each on the rest — visibly shorter, no cards unless asked, same numbers.

8. **Stay in the conversation.** The read is an opening, not a terminus. Offer next explorations tied to what moved ("dig into the canonical regression?", "want the watch-list items expanded?"). Hand off when asked: "raise these as tickets" → the dev-handoff skill; "I need this as a client document" → the technical-seo-audit skill; "what should I fix first overall?" → the what-to-fix-first skill.

9. **Optional dashboard — only if the user wants it.** Offer once ("want this as a shareable dashboard for the client?"). If yes: render natively where the assistant supports inline interactive output; otherwise (and for anything the user will send on) deliver a **self-contained HTML file** — no external dependencies, no assistant-specific machinery — mirroring the read: the headline, wins/regressions/watch-list, the cards with change arrows, and the GA/GSC overlay where present.

## Failure modes

- **`hasPreviousAudit` is false:** no change story exists. Say so plainly, deliver a current-state read as the baseline, recommend scheduled crawls. Never fabricate a comparison.
- **Sitebulb core capability missing** (likely a renamed/removed tool): the preflight catches it. Name the capability expected, show what's connected instead, and stop — never substitute another tool's data.
- **The change list and the hint rows disagree** (a delta in one, absent in the other): surface the discrepancy rather than the flattering reading; a probable renamed field or measurement gap, not a clean result.
- **Material scope shift between the pair:** lead with it; compare ratios, not raw counts (step 2).
- **No GA/GSC attached:** the change story still ships; the overlay is skipped and the read says the connection would sharpen it. Missing traffic data is never zero traffic.
- **A URL sample comes back empty where the change row shows a non-zero count:** probable wrong/renamed `urlFilterId` — corroborate against the row and surface it. (Shorter-than-count samples are expected; zero rows against a non-zero count is the failure signal.)
- **User asks for a crawl:** read-only — respond per shared-core rule 8 and offer to proceed on the latest pair.

## Reference

- `references/shared-core.md` — Sitebulb data-handling rules, § Tool binding capability map + preflight, and the framing-interview ground rules. Read before any data pull.
- `references/context-emphasis.md` — the reframe rules: situation lead stories (routine check and traffic decline especially), type lift/demote, precedence, refusal default. Read before the interview.
- `scripts/score_effort.py` — the shared deterministic scorer, used **only** when an effort estimate is explicitly wanted (step 6); carries the recalibrated duration table. Never hand-compute an estimate. (`scripts/test_score_effort.py` is its suite; `references/effort-scoring.md` is the spec; `references/hint-map.csv` the catalogue, read by the script, not into context.)
