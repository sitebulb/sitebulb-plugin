---
name: what-to-fix-first
description: "Produce a prioritised read of a Sitebulb audit — the 3–5 issue clusters most worth fixing for this business in this situation — by interviewing for business context, sweeping triggered hints, and scoring impact (severity × section tier × effective coverage × traffic linkage) against effort (fix archetype, S–XL, owner, indicative duration), with context reframing what leads but never the scores. Use for \"what should I fix first\", \"what's wrong with this site\", \"where do I start\", \"prioritise this crawl/audit\", \"quick wins\", \"what's worth my attention\", or any effort-vs-impact triage of Sitebulb findings. Not for raising dev tickets (dev-handoff), change-over-time stories (what-changed), or client documents (technical-seo-audit)."
---

# What To Fix First

Opens as a diagnosis, not a data pull. The job is to help the user understand what's wrong with their site and what's worth their attention — for *this* business, in *this* situation. Data pulls, scoring and the ranked output are in service of that: the skill establishes context first, delivers a conversational prioritised read, then stays in the conversation guiding next explorations. It is the front door of the Sitebulb skill ecosystem.

Before doing anything else, read `references/shared-core.md` — the data-handling rules (noise filtering, sample semantics, score semantics) and its § Tool binding (resolve Sitebulb capabilities to the live tools, plus the preflight) without which the output is wrong, not just worse. Then read `references/context-emphasis.md` — the reframe rules this skill's identity rests on.

## Preconditions

1. **A Sitebulb MCP is connected** (Desktop and Cloud are tool-for-tool identical). If not, say so and stop — there is no fallback data source.
2. **The MCP is read-only — it cannot trigger crawls.** If the user asks for fresh data, tell them the latest finished audit is from <date> and a new crawl must be started in Sitebulb itself; offer to proceed on the existing audit.
3. **A finished audit exists for the target project.** Name the most recent finished one and its date so the user knows what evidence the read rests on.

## The context interview

Ask once, up front, before any data pull — one round only, per the shared-core interview rules (skip what's already known or evident; challenge non-answers; then proceed on stated assumptions). Four things, conversationally, not as a form:

- **Business type:** ecommerce, publisher/news/content, SaaS, lead-gen, marketplace, education, business/services, or affiliate — plus an *enterprise* modifier flag that can sit on any type.
- **Situation** (up to two; a causally-linked pair becomes the lead hypothesis): traffic decline, migration/redesign just happened, pre-migration, new client onboarding, routine check, deadline-driven, international expansion.
- **Constraints:** CMS, dev availability, team shape — these feed the effort engine's modifiers (`cms_self_serve_metadata`, `low_dev_availability`, `ample_dev_capacity`, `solo_no_content_team`, `host_managed_infra`). Only pass a modifier the conversation has actually surfaced; never invent one to complete the picture.
- **Role:** agency, independent, or in-house — sets voice and who the read is written for.

**Refusal default:** if the user skips, passes, or doesn't know, proceed on the pure tier ordering with no reframe — and say that's what's happening ("no context given, so this is the raw SEO-relevance ranking"). Never stall on an unanswered interview.

**Conversational mode:** "what should I fix first?" with context already established (or declined) goes straight to the ranked read — no ceremony, no re-interviewing.

## Building the read

0. **Preflight capabilities** (shared-core § Tool binding). *Core — stop if unmatched:* list a project's audits; list an audit's hint categories; list triggered hints per category (category is a required input, so the category list is load-bearing). *Peripheral — note the gap and carry on:* the per-hint affected-URL sample list; single-URL column reads (traffic + depth for step 3); GA/GSC report availability; `learnMoreUrl`.
1. **Resolve project and latest finished audit.** Confirm with the user if ambiguous. Record whether GA/GSC data is attached to the audit (the report catalogue shows it) — this gates the traffic term — and whether `hasPreviousAudit` is true (the traffic-decline situation needs to know).
2. **Category sweep.** List the audit's hint categories, then pull triggered hints per category — leaving the Accessibility lane out of the read (it is a parked workstream; at most signpost it, e.g. for education sites). Apply the noise filter: drop `severity: none` rows. Keep `warningType: opportunity` rows visible to the reframe step (some situations demote them wholesale) but let them score. Hint rows carry everything scoring needs — `urlFilterId`, severity, `coverage`, `affectedUrlsCount`, indexable/not-indexable splits, `learnMoreUrl` — no per-hint follow-up calls at this stage.
3. **Score both axes by calling `scripts/score_effort.py`** — never hand-compute the join or either axis's arithmetic (`references/effort-scoring.md` is the spec it implements). Pass every surviving hint as JSON: `url_filter_id` straight off the row (the canonical join; title and `learn_more_url` as fallbacks), `severity`, `coverage`, `affected_urls` = the row's `affectedUrlsCount`, `indexable_urls` = its indexable count. Run-level: `modifiers` (only those the conversation surfaced) and `gates` from the context layer — `Rendered` on for ecommerce/marketplace or evident JS-framework usage, `International` on for international expansion or evident multi-locale usage, `AMP` on evident AMP usage. The script returns per hint the impact score, effort `size`/`duration`/`owner`/`basis`, and flags (`gated_off`, `must_fix`); unmapped hints (`matched: false`) get no effort block — never guess — and a set `drift_warning` means the map may be stale for this Sitebulb version, so surface it.

   ```bash
   echo '{"modifiers":["low_dev_availability"],
          "gates":{"Rendered":true},
          "hints":[{"url_filter_id":"broken_internal_urls","title":"Broken internal URLs",
                    "severity":"High","coverage":5.8,
                    "affected_urls":60,"indexable_urls":55,
                    "learn_more_url":"https://sitebulb.com/hints/links/broken-internal-urls/"}]}' \
     | python3 scripts/score_effort.py
   ```
4. **Bounded traffic enrichment + homepage check** — only if GA/GSC is attached; otherwise skip, keep every multiplier at the neutral ×1, and say the read would sharpen with the connection. Rank hints by the pre-traffic impact, take the top 5–8, and for each fetch a capped sample (~5) of its indexable affected URLs' column data (single-URL reads). Keep the cap tight: each single-URL read returns the full column set (a very large payload), so a generous sweep exhausts context long before it exhausts the URL list — sum what the capped sample shows and label the sample size in the read. Sum GSC clicks across the sample (GA sessions as fallback) and note whether the site root (`Depth == 0` — the homepage is stored without a trailing slash, so match on depth, not the string) is in any Critical/High hint's affected set. Re-run the scorer with `traffic_clicks`/`traffic_sessions` and `homepage_affected` added. The long tail stays neutral by design — bounded calls, not a sweep.
5. **Cluster.** Group hints that share a fix mechanism — same archetype and section tell one story (the canonical-correctness per-instance hints are one cluster, not six line items). A cluster's impact is its highest-scoring member, never a sum (summing rewards fragmentation); its effort is the dominant archetype's, sized on the combined affected count where the archetype is banded. `must_fix` hints pin their cluster above the matrix.
6. **Reframe per `references/context-emphasis.md`.** The situation picks which clusters lead and the narrative arc; the type adjusts vocabulary, examples and tiebreaks. Scores are never touched. Demotions are honest and explicit: "this scored high overall, but matters less for you because...". Under the refusal default this step is a no-op and the read says so.
7. **Present the prioritised read** — conversational analysis first, then the evidence cards. Three to five clusters, must-fix pins first.

   **Voice — the scoring machinery never appears in the output.** The people reading this did not author the skill. Impact scores, tiers, section weights, axes, bands, archetype numbers, gate names, flag names and the scorer's basis lines are internal working — use them to decide, never to explain. Translate every one into plain consequence: not "scores 0 on the organic-impact axis" but "broken pages can't rank, so the direct search loss is small — the cost here is lost link equity and user trust". Demotions stay honest but in the user's terms: "this touches every page on the site, but it's a best-practice item with no direct ranking effect, so it's not in your top set".

   **The analysis** — per cluster:
   - **Why it matters for this business** — the consequence in the user's context. Where traffic data informed the ranking, say what it showed ("your /download/ page earns 77 clicks a month and has no meta description").
   - **What fixing it takes** — owner, size and indicative duration from the scorer, always paired with what the work actually is ("map and deploy 28 redirects — half a day to a day including sign-off"). A duration with no description of the work reads as inflated or arbitrary. Where a bulk/template route beats the per-URL grind (400 meta descriptions are prioritised and templated, not hand-written one by one), describe the realistic path and note the estimate covers it. Label everything planning guidance, never a commitment; where dev availability stretched a duration, say it's queue time; where the fix is host-controlled, flag it and sequence it later. No Gantt charts, no phases, no generated dates — ever.

   **The evidence cards** — after the analysis, present each featured hint visually, one card per hint, mirroring the Sitebulb hint layout so users recognise it from the app:
   - Header: severity pill (Critical/High/Medium/Low) + issue-type tag (Issue / Potential Issue / Opportunity) + the hint title.
   - Stat row: **URLs** (the row's true `affectedUrlsCount`, with the change vs previous audit as an up/down arrow), **Percentage** (coverage), **Indexable** and **Not Indexable** (with changes) — omit the indexable pair where the hint type doesn't carry the split (the Sitebulb UI omits those boxes too); for duplicate-content hints the affected set is wholly indexable by design — use that in the analysis rather than showing zeros.
   - One or two plain-language sentences from the hint description.
   - **Up to 10 sample URLs**, labelled as a sample ("Sample URLs (10 of 177)"), chosen for variety across templates/sections, fetched via the hint's `urlFilterId`.
   - Footer: the export pointer ("Full list (N URLs): export from this hint's Affected URLs view in the Sitebulb app") and the Learn More link (`learnMoreUrl`).

   Render the cards with whatever inline visual/rich output the assistant supports; where none is available, the same card as clean markdown (heading, stat line, sample list, footer) — the content is identical either way (portability rule 3).
8. **Stay in the conversation.** The read is an opening, not a terminus. Offer guided next explorations tied to what was found ("dig into the canonical cluster?", "see which of these touch your top-traffic pages?", "want the demoted items too?"). Hand off when asked: "want these as dev tickets" → the dev-handoff skill; "need this as a client document" → the technical-seo-audit skill.

## Failure modes

- **Sitebulb core capability missing** (likely a renamed/removed tool): the preflight catches it. Name the capability expected, note the tool may have changed in a newer Sitebulb release, show what's connected instead, and stop — never substitute another tool's data.
- **A URL query returns empty where the hint row shows a non-zero count:** a probable wrong/renamed `urlFilterId` or reshaped field, not a clean result. Corroborate against the row's `affectedUrlsCount` and surface the discrepancy. (A sample *shorter* than the count is expected — samples cap at 50; the failure signal is zero rows against a non-zero count.)
- **No GA/GSC attached:** the read still works — traffic stays neutral, the homepage check is skipped, and the output says the ranking would sharpen with the connection. Never treat missing traffic data as zero traffic (shared-core rule 4).
- **Traffic-decline situation with `hasPreviousAudit: false`:** no change story exists. Say so plainly, deliver the current-state read as the hypothesis space ("things that *could* be suppressing traffic"), and recommend scheduled crawls.
- **Many unmapped hints / `drift_warning`:** flag possible map staleness for this Sitebulb version rather than treating each as a one-off; the read still ships, with those items carrying no effort block.
- **User asks for a crawl:** read-only — respond per shared-core rule 8 and offer to proceed on the latest finished audit.

## Reference

- `scripts/score_effort.py` — the deterministic two-axis scorer: `urlFilterId`/title/URL join, effort banding + modifiers + floor/cap, and the impact formula (severity 8/4/2/1 × section weight with conditional gating × effective coverage × traffic linkage, plus the homepage must-fix pin). Call it in steps 3–4; never hand-compute. (`scripts/test_score_effort.py` is its suite.)
- `references/shared-core.md` — Sitebulb data-handling rules, § Tool binding capability map + preflight, and the framing-interview ground rules. Read before any data pull.
- `references/context-emphasis.md` — the reframe rules: type lift/demote lists, situation lead stories, precedence, gating, refusal default. Read before the interview.
- `references/effort-scoring.md` — archetypes, bands, modifiers, durations, and the locked impact mechanics: the spec the script implements.
- `references/hint-map.csv` — the classified catalogue (358 hints, `urlFilterId`-keyed). Read by the script, not into context.
