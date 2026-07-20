# The Audit Document — Deliverable Spec

Self-contained structural spec for the client-facing technical SEO audit document. It describes *what the document is*, independent of any assistant's document tooling: produce it as a Word (.docx) file with whatever document-generation capability the environment provides. Modelled on real agency audit deliverables; the register is a good consultant explaining, not a tool reporting.

Everything below is client-facing except the review comments, which are consultant-facing (see § Review comments). The presentation bans from SKILL.md § The document apply to every word in the file, comments included.

## Document skeleton

1. **Cover block** — title ("Technical SEO Audit — <client/site name>"), the site audited, date prepared, prepared-by line left as a placeholder for the consultant ("Prepared by: ______"), and the crawl date the evidence rests on ("Based on a Sitebulb crawl completed <date>"). No logos or theming — branding is deliberately out of scope (a follow-on concern); the consultant applies their own.
2. **Executive summary** — one to three short paragraphs that answer the commissioning question in plain language. Not a generic "we audited the site": if the audit was bought after a traffic decline, the summary says what the crawl can and cannot say about the decline; if for onboarding, it is the state-of-the-nation in three sentences; if pre-migration, it frames the document as the baseline and the fix-before-you-migrate list. Close with one sentence on how to read the document ("the issues below are the N things most worth acting on, in order; each explains what we found, what it means for you, and what fixing it involves").
3. **Scope note** — one short paragraph, part of or immediately after the exec summary: what this audit deliberately leaves aside and why, in the client's terms. This is where honest demotions live ("site security items are present but well-managed and have little bearing on your search performance, so they are not in the main set"). Never silently drop a demotion the client might hear about elsewhere.
4. **Summary of issues** — a table: item title × priority, in document order. Priority is the severity-mapped word (Critical / High / Medium / Low), never a number or score. This table is the document's contract: the sections that follow expand it, in the same order.
5. **The items** — one section per item, 5–10 of them (per-item anatomy below).
6. **Recommendations & next steps** — the prioritised read in document form: a compact restatement of each item's recommendation with its owner, size word (Small / Medium / Large / a major piece of work) and indicative duration, explicitly labelled planning guidance to be confirmed with the people doing the work. Sequence by the document's order; note dependencies in prose where they exist ("the redirect work is best done alongside the template fix in item 3"). **No Gantt charts, no phases, no generated dates, no timelines.** Close with what a follow-up looks like (a re-crawl after fixes; the app shows what changed).

## Per-item anatomy

Each item section carries, in order:

1. **Title** — plain-language, problem-first ("Broken links are sending visitors and search engines to dead pages"), not the internal hint name. The hint title may inform it; field vocabulary never appears.
2. **What we found** — the evidence, led by the true count: the affected-URL count as reported by the crawl (always the hint row's true count, never a count of sample rows), coverage in plain terms where it helps ("around one page in twelve"), and the change since the previous audit where the spine wants a change story ("up from 51 at the last crawl in June"). Where the issue type doesn't measure an indexable split, say nothing about indexability rather than implying zeros; duplicate-content findings are described as affecting pages search engines *can* index — that is what makes them matter.
3. **Why it matters for you** — the mechanism and the consequence in this client's terms, at the stated reader's technical level. Draw on the hint's knowledge-base description; link the knowledge-base article as further reading ("Sitebulb's guide to this issue: <learnMoreUrl>"). One reader-calibrated paragraph beats three generic ones.
4. **Sample URLs** — up to 10, chosen for variety across templates/sections of the site, under an explicit sample label: "A sample of 10 of the 421 affected URLs:". Then the export pointer, always to the app and only the app: "The full list can be exported from this issue's Affected URLs view in the Sitebulb app."
5. **Recommendation** — under the item's Recommendation heading, state the action directly as a full sentence ("Map and deploy redirects for the 28 dead pages, prioritising the 6 that still earn traffic.") — never repeat a "Recommendation —" label under a heading that already says Recommendation. Then owner ("this is developer work" / "your content team can do this in the CMS"), the size word and indicative duration, always paired with what the work actually is and the realistic fix path — where a bulk/template route beats the per-URL grind (400 missing meta descriptions are prioritised and templated, not hand-written one by one), describe that route and note the estimate covers it. Where low dev availability stretched a duration, say the stretch is queue time; where the fix sits with an external host, flag it as outside the client's direct control and sequence it accordingly.

## Register calibration

The commissioning interview's reader answer sets the register; non-technical is the default.

- **Non-technical (marketing director, founder, procurement):** mechanism explained by consequence ("search engines keep a copy of your site; these pages are telling them not to"), no HTTP status codes without a gloss, analogies where they genuinely clarify.
- **Technical (dev lead, in-house SEO):** status codes, directives and header names are fine; keep the *why it matters* — technical readers still need the priority case, not just the finding.
- **Mixed/unknown:** write for the non-technical reader; technical detail goes in the recommendation where the doer needs it.

Whatever the register: no scoring vocabulary, no tool or field names, no internal flags or gates, anywhere.

## Review comments

Consultant-facing notes, inserted as native document comments anchored to the passage each concerns; where the environment cannot write native comments, use visually distinct highlighted paragraphs in the form `[REVIEW: …]` that the consultant deletes. Placements:

- On sample-URL blocks where the sample raises a genuine question — a pattern the consultant should confirm, examples that look deliberate rather than broken, a mix the client will ask about. At minimum, one sample spot-check comment per document, on the most load-bearing item. Sample blocks whose contents are exactly what the item describes need no comment.
- On any item selected, demoted, excluded or framed off the commissioning context, where reasonable consultants could differ: what was decided, on what stated context, what would reverse it.
- On any recommendation whose fix path assumes something about the client's stack: verify against the actual CMS/platform before committing.
- Where a screenshot or worked example from the live site would materially strengthen a section: say so — the consultant can capture what the crawl data cannot.
- On the exec summary, when the refusal default fired: the assumptions proceeded on, so the consultant can revisit them.

Comments are working notes in plain SEO language, honest about uncertainty, never boilerplate — a comment that could be pasted onto any item verbatim shouldn't exist. Three to eight well-placed comments is typical; judgment-call and can't-see-it notes carry more value than routine spot-check reminders, so never crowd them out to hit a per-item quota.

## What never appears

- Scores, tiers, weights, axes, bands, archetype numbers, gate/flag/field/tool names, basis lines — internal working translates to plain consequence.
- "None of these pages are indexable" readings of an unmeasured indexable split; rendered 0/0 indexable statistics of any kind.
- A sample presented as the full list, or counts derived from sample rows.
- Any export destination other than the Sitebulb app's Affected URLs view.
- Gantt charts, phases, generated dates, delivery timelines.
- More than ten items, or padding to reach five.
