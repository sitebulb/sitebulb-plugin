---
name: technical-seo-audit
description: "Produce the client-facing technical SEO audit document from a Sitebulb project's latest finished audit: a focused Word working draft of 5–10 issues — never encyclopaedic — selected and ordered by why the audit was commissioned (traffic decline, redesign/migration, onboarding, due diligence), written for the stated reader, each issue carrying its true affected count, labelled sample URLs, a Sitebulb-app export pointer, a knowledge-base link, and a recommendation with owner and indicative effort. Ships seeded with consultant-facing review comments marking where human judgment is needed. Use whenever the user asks for a 'technical SEO audit', 'client audit', 'audit document', or 'audit deliverable', says 'write up the audit for [client]' or 'run the audit on [project]', or hands off from a prioritised read ('need this as a client document'). Not for conversational what-to-fix triage (what-to-fix-first), change-over-time stories (what-changed), or dev tickets (dev-handoff)."
---

# Technical SEO Audit

Produces the deliverable an agency consultant or freelancer sells as a one-off engagement: the client-facing technical audit document. Focused, not encyclopaedic — **five to ten items maximum**, the most important issues for *this* client in *their* specific situation. The temptation to be exhaustive is the failure mode this skill exists to refuse: a 40-issue laundry list is what the client could have got from any crawler export; the 5–10 items that matter, explained in their terms and ordered by why they bought the audit, is what they paid a consultant for.

The output is a **working document, not a finished ta-da deliverable**. If a consultant ships it without checking or improving anything themselves, they are not doing their job — the document says so where it matters, via review comments anchored to the passages that need human judgment (see § The review layer). The consultant's name goes on this document, not the assistant's.

Before doing anything else, read `references/shared-core.md` — the data-handling rules and its § Tool binding (resolve Sitebulb capabilities to the live tools, plus the preflight) without which the output is wrong, not just worse. Then read `references/context-emphasis.md` — the reframe rules that decide what goes in the document. `references/document-template.md` is the deliverable spec; read it before drafting.

## Preconditions

1. **A Sitebulb MCP is connected** (Desktop and Cloud are tool-for-tool identical). If not, say so and stop — there is no fallback data source.
2. **The MCP is read-only — it cannot trigger crawls.** If the user wants the audit run on fresh data, tell them the latest finished audit is from <date> and a new crawl must be started in Sitebulb itself; offer to proceed on the existing audit.
3. **A finished audit exists for the target project.** Name the most recent finished one and its date — the document's evidence rests on it, and the document itself states the crawl date.

## The commissioning interview

The context layer is load-bearing here: the same crawl produces a *different document* for a different commissioning context. Ask once, up front, before any data pull — one round only, per the shared-core interview rules (skip what's already known or evident; challenge non-answers; then proceed on stated assumptions). Four things, conversationally, not as a form:

- **Why was the audit commissioned?** Traffic decline, redesign/migration (done or planned), new-client onboarding, due diligence, deadline-driven, international expansion, or a routine engagement. This maps to the situation layer in `references/context-emphasis.md` (up to two; a causally-linked pair becomes the lead hypothesis) and becomes the document's narrative spine — the exec summary answers *this question*, and item selection and ordering serve it.
- **What kind of business is the client?** Ecommerce, publisher/news/content, SaaS, lead-gen, marketplace, education, business/services, or affiliate — plus the *enterprise* modifier on any type. Sets vocabulary, examples, tiebreaks, and the Rendered gate.
- **Who reads the document?** Their role and technical level — a marketing director, an in-house dev lead, a founder, a procurement/due-diligence audience. Non-technical is the default register. The reader shapes voice, how much mechanism each explanation carries, and tiebreaks item selection toward what the reader can act on.
- **Constraints:** the client's CMS, dev availability, team shape — these feed the effort engine's modifiers (`cms_self_serve_metadata`, `low_dev_availability`, `ample_dev_capacity`, `solo_no_content_team`, `host_managed_infra`). Only pass a modifier the conversation has actually surfaced; never invent one.

**Refusal default:** if the user skips, passes, or doesn't know, proceed on the pure tier ordering with no reframe — say so in the chat, and record the proceeded-on assumptions as review comments in the document (§ The review layer) so the consultant can revisit them.

## Building the item set

The engine is What To Fix First's, unchanged — same sweep, same scorer, same clustering. Steps 0–5 below match that skill's; never hand-compute what the script computes.

0. **Preflight capabilities** (shared-core § Tool binding). *Core — stop if unmatched:* list a project's audits; list an audit's hint categories; list triggered hints per category. *Peripheral — note the gap and carry on:* the per-hint affected-URL sample list; single-URL column reads; GA/GSC report availability; `learnMoreUrl`.
1. **Resolve project and latest finished audit.** Confirm with the user if ambiguous. Record whether GA/GSC data is attached (gates the traffic term) and whether `hasPreviousAudit` is true. The traffic-decline and migration spines need the change story; other spines use per-hint deltas opportunistically.
2. **Category sweep.** List the audit's hint categories, then pull triggered hints per category — leaving the Accessibility lane out (parked workstream; at most a one-line signpost, e.g. for education clients). Drop `severity: none` rows. Keep `warningType: opportunity` rows visible to the selection step — some spines demote them wholesale. Hint rows carry everything scoring needs; no per-hint follow-up calls at this stage.
3. **Score both axes with `scripts/score_effort.py`** — pass every surviving hint as JSON exactly as `references/effort-scoring.md` specifies: `url_filter_id` off the row (title and `learn_more_url` as fallbacks), `severity`, `coverage`, `affected_urls` = the row's `affectedUrlsCount`, `indexable_urls` = its indexable count, `not_indexable_urls` = its not-indexable count (both counts, so the scorer can detect an unmeasured split). Run-level: `modifiers` (only those surfaced) and `gates` from the context layer — Rendered for ecommerce/marketplace or evident JS-framework usage, International for the international-expansion spine or evident multi-locale usage, AMP on evident AMP usage. Unmapped hints (`matched: false`) get no effort block — never guess; a set `drift_warning` means the map may be stale for this Sitebulb version, so tell the user.

   ```bash
   echo '{"modifiers":["low_dev_availability"],
          "gates":{"Rendered":true},
          "hints":[{"url_filter_id":"broken_internal_urls","title":"Broken internal URLs",
                    "severity":"High","coverage":5.8,
                    "affected_urls":60,"indexable_urls":55,"not_indexable_urls":5,
                    "learn_more_url":"https://sitebulb.com/hints/links/broken-internal-urls/"}]}' \
     | python3 scripts/score_effort.py
   ```
4. **Bounded traffic enrichment + homepage check** — only if GA/GSC is attached; otherwise skip, keep multipliers neutral, and note in the chat (not the document) that the selection would sharpen with the connection. Rank by pre-traffic impact, take the top 5–8 hints, fetch a capped sample (~5) of each's indexable affected URLs' column data. Keep the cap tight — each single-URL read returns the full column set and a generous sweep exhausts context. Sum GSC clicks (GA sessions fallback), check whether the site root (`Depth == 0`) sits in any Critical/High hint's affected set, re-run the scorer with `traffic_clicks`/`traffic_sessions` and `homepage_affected`. Bounded calls, never a sweep.
5. **Cluster.** Group hints sharing a fix mechanism — same archetype and section tell one story. A cluster's impact is its highest-scoring member, never a sum; its effort is the dominant archetype's, sized on the combined affected count where banded. `must_fix` hints pin their cluster into the document regardless of ordering below.
6. **Select and order the 5–10 items.** This is where this skill diverges from the conversational read:
   - The **commissioning spine picks and orders**: the situation's lead story (per `references/context-emphasis.md`) decides which clusters make the document and the sequence they're told in; the business type adjusts vocabulary, examples and tiebreaks; the reader tiebreaks toward actionability.
   - **Enforce the cap.** Five to ten items. If more clusters seem to deserve inclusion, they don't — fold true siblings into one item, name the strongest, and let the rest go. If fewer than five clusters genuinely matter, ship fewer with a short "what we checked and found healthy" paragraph rather than padding: a padded audit teaches the client to skim.
   - **Reframe, never reweight.** Scores stay pure; selection and ordering are the context's work. When the spine demotes or excludes a high scorer, the demotion is honest and lives in the document's *scope note* (one short paragraph in the intro: what this audit deliberately leaves aside and why) or in a review comment for the consultant — in the client's terms, never scoring vocabulary.
   - Gated-off sections stay out unless their gate is on; ungated conditional findings never appear as items.

## The document

Full structural spec, section by section: `references/document-template.md`. The shape (modelled on real agency audits): a cover block; an executive summary that answers the commissioning question in plain language; a summary-of-issues table (item title × priority — priority as the severity-mapped word, never a score); one detailed section per item; a closing recommendations/next-steps section that is the prioritised read in document form — owner, size and indicative duration per item as planning guidance, no Gantt charts, no phases, no generated dates.

Per item, always: a plain-language explanation of what the issue is and why it matters *for this client* (drawing on the hint description, with the `learnMoreUrl` as a "further reading" link — the knowledge base is the explanation engine); the evidence — the true count from the hint row's `affectedUrlsCount`, the change vs previous audit where a spine wants it, up to 10 sample URLs **labelled as a sample** ("a sample of 10 of the 421 affected URLs"), and the export pointer ("the full list can be exported from this hint's Affected URLs view in the Sitebulb app" — the Sitebulb app is the only export destination this skill ever names); and a recommendation stating the action directly, with owner and effort guidance, every duration paired with what the work actually is and the realistic fix path (prioritise-and-template where that is how anyone would really do it — a bare duration in a client document reads as inflated or arbitrary).

**Voice.** Client-facing, calibrated to the stated reader; non-technical by default — the register of a good consultant explaining, not a tool reporting. The scoring machinery never appears: impact scores, tiers, section weights, axes, bands, archetype numbers, gate names, flag names, field names, tool names and the scorer's basis lines are internal working — translate every one into plain consequence. Indexability statements obey shared-core rule 9: a 0/0 split on a split-less hint type is never "none of these pages can be indexed"; duplicate-content sets are wholly indexable by design — say that in prose where it matters, never render the zeros.

**Delivery.** Produce the document as a Word (.docx) file using whatever document tooling the assistant's environment provides — the template reference describes structure and content in full, deliberately independent of any assistant's internal document machinery. Where the environment cannot produce a Word document, produce the nearest rich-document format it can and say so; the structure is identical.

## The review layer

The document ships seeded with **consultant-facing review comments** — native Word comments anchored to the passage each concerns, so nothing ships to the client without the consultant touching each one. They are the working-document principle made concrete. Four kinds, placed where the skill genuinely wants a human check — never decoratively:

1. **Sample verification** — on sample blocks where the sample raises a genuine question (at minimum one per document, on the most load-bearing item): spot-check and confirm the pattern before this goes out.
2. **Judgment calls the consultant should own** — where an item was selected, demoted, excluded or framed off the commissioning context: what was decided, on what stated context, and what would reverse it.
3. **Things Sitebulb can't see** — verify a fix path against the client's actual CMS or stack before committing to it; where a screenshot of an example page would strengthen the section, say so (the assistant cannot take one; the consultant can).
4. **Assumptions under the refusal default** — anything the consultant declined to answer that the document proceeded on.

Comments speak plain SEO — the consultant didn't author this skill either, so the presentation bans apply inside comments too. Where the environment cannot write native document comments, use a visually distinct inline marker style (e.g. highlighted `[REVIEW: …]` paragraphs) the consultant deletes — same content, uglier carrier.

**The covering note** goes in the chat, not the document: this is a working draft; the comments mark where your judgment is needed; check, edit and improve it before it carries your name. Then stay in the conversation — offer to rework an item's framing, swap an item for a demoted one, adjust register for a different reader, or hand off ("want these as dev tickets" → the dev-handoff skill; "what should we tackle first ourselves" → the what-to-fix-first skill).

## Failure modes

- **Sitebulb core capability missing:** the preflight catches it — name the capability, note the tool may have changed in a newer Sitebulb release, show what's connected, stop. Never substitute another tool's data.
- **A URL query returns empty where the hint row shows a non-zero count:** probable wrong/renamed `urlFilterId`, not a clean result — corroborate against `affectedUrlsCount` and surface the discrepancy (a sample *shorter* than the count is expected; zero rows against a non-zero count is the failure signal).
- **Traffic-decline or migration spine with `hasPreviousAudit: false`:** no change story exists. Say so plainly in chat, frame the document as the hypothesis space ("the things that could be suppressing traffic") with that framing explicit in the exec summary, and recommend scheduled crawls.
- **No GA/GSC attached:** the document still ships — traffic stays neutral, and the chat (not the document) notes the selection would sharpen with the connection.
- **Many unmapped hints / `drift_warning`:** flag possible map staleness in chat; affected items carry no effort estimate in the document rather than a guessed one, with a review comment saying why.
- **The user asks for more than ten items:** push back once — the cap is the skill's value — then, if they insist, deliver their count with a review comment on the exec summary noting the document now trades focus for coverage.
- **User asks for a crawl:** read-only — respond per shared-core rule 8 and offer the latest finished audit.

## Reference

- `references/document-template.md` — the deliverable spec: section-by-section structure, per-item anatomy, the review-comment placements, register calibration. Read before drafting.
- `scripts/score_effort.py` — the deterministic two-axis scorer shared with what-to-fix-first; call it in steps 3–4, never hand-compute (`scripts/test_score_effort.py` is its suite).
- `references/shared-core.md` — Sitebulb data-handling rules, § Tool binding + preflight, interview ground rules. Read before any data pull.
- `references/context-emphasis.md` — the reframe rules: type lift/demote, situation lead stories, precedence, gating, refusal default. Read before the interview.
- `references/effort-scoring.md` — archetypes, bands, modifiers, durations, impact mechanics: the spec the script implements.
- `references/hint-map.csv` — the classified catalogue (`urlFilterId`-keyed), read by the script, not into context.
