# Context Layer — Emphasis Rules

How business context reshapes the prioritised read. Agreed rules (9 Jul 2026), consumed by What To Fix First; Progress Monitor and Technical SEO Audit inherit them.

## How the rules act

**Reframe, never reweight.** The impact score stays pure — the scorer's arithmetic is untouched by anything here. Context acts *after* scoring: it selects which clusters lead, what is said about them, and what gets demoted to a footnote. When context demotes something that scored high, say so honestly: "this scored high overall, but matters less for you because...". Never hide a high scorer silently.

**Precedence.** Situation trumps business type. The situation is why the user is here today; the type is the permanent backdrop. The situation picks the clusters and the narrative arc; the type adjusts vocabulary, examples, and tiebreaks between similar-impact clusters (migration + ecommerce → the redirect story told through dead SKUs and category URLs first).

**Multiple situations.** Accept up to two. Where they are causally linked ("traffic tanked right after our migration"), the link itself becomes the lead hypothesis and drives the whole read ("did the migration cause the decline?"). Beyond two, push back and ask what matters most.

**Enterprise is a modifier, not a type.** It can sit on any business type. When flagged: lift crawl budget, template-level fix framing, legacy-redirect accumulation, and hreflang; expect the dev-queue reality and pair naturally with the `low_dev_availability` effort modifier. Enterprise ecommerce is ecommerce + enterprise, not a ninth category.

**Refusal default.** If the user skips the questions, passes, or genuinely doesn't know, proceed on the pure §11 tier ordering with no reframe — and say that's what's happening. Never stall the skill on an unanswered interview.

**Conditional-section gating.** The context decides the scorer's `gates`: **Rendered** gates on for ecommerce, marketplace, or any JS-framework signal. **International** gates on for the international-expansion situation, or evident hreflang/multi-locale usage. **AMP** gates on evident AMP usage. Ungated conditional sections score 0 (returned flagged `gated_off`, never silently dropped).

## Business types — lift / demote

Lift = lead with it, expand on it, tiebreak toward it. Demote = footnote it, soften the framing, or skip it in a 5–10 item deliverable. Neither touches the score.

**Ecommerce**
- Lift: duplicate content (variants, parameters), faceted-navigation indexability, crawl budget, product structured data, redirects/404s from dead SKUs, internal linking to category and product pages, Response vs Render.
- Demote: thin-content hints on product pages (PDPs are naturally lean — frame, don't scold), hreflang unless they trade internationally.

**Publisher / news / content**
- Lift: on-page (headlines, titles), orphans and archive depth, XML sitemaps (freshness), Article structured data, pagination, crawl budget on large archives.
- Demote: conversion-page framing, product schema.

**SaaS**
- Lift: on-page and content quality (blog/docs carry the SEO), docs and app-subdomain indexability leaks, duplicate content across documentation versions.
- Demote: crawl budget and faceted-navigation concerns (sites are usually small).

**Lead-gen**
- Lift: on-page for service/conversion pages, near-duplicate location landing pages (doorway-page risk), internal linking to money pages, mobile-friendly.
- Demote: crawl budget, pagination.

**Marketplace** (ecommerce at UGC scale)
- Lift: crawl budget (hard), indexation of internal search / facet / listing pages, thin and duplicate listings, expired-listing 404s and redirects, Response vs Render.
- Demote: very little — this is the type where almost everything is live.

**Education**
- Lift: structural sprawl (orphans, depth, subdomains), stale and annually-cycling pages (course URLs → redirects), duplicate content from devolved CMS publishing.
- Demote: commercial schema. (Accessibility genuinely matters for this type but remains the parked lane — at most a signpost to it.)

**Business / services (brochure)**
- Lift: on-page basics, LocalBusiness schema, mobile-friendly, HTTPS/trust framing.
- Demote: crawl budget, hreflang, pagination — small-site noise.

**Affiliate**
- Lift: thin/duplicate content (doorway risk), internal-link silo integrity, outbound link hygiene (broken externals, affiliate-link nofollow), review/product schema.
- Demote: little beyond big-site plumbing.

## Situations — the lead story

**Traffic decline**
- Lead: the change story as hypothesis-testing — indexability regressions, noindex/canonical/robots accidents, redirect breakages, lost & found deltas, GSC/GA overlay to locate *where* the decline sits. Scope sanity-check before believing any trend.
- Frame every finding as "could this explain the drop?" — and be honest when nothing in the crawl could (algorithmic or competitive causes are outside Sitebulb's sight).
- First-crawl caveat: there may be no lost & found — if `hasPreviousAudit` is false, say so plainly, fall back to a current-state read framed as the hypothesis space ("these are the things that *could* be suppressing traffic"), and recommend scheduled crawls so the next decline has a trend behind it.
- Demote: opportunity-class hints (`warningType: opportunity`) definitively; potential-issue-class hints by judgement — demote unless one plausibly explains the drop (e.g. a potential-issue canonical hint on the declining section stays in play).

**Migration / redesign just happened**
- Lead: redirects (broken, chains, loops), scope change, indexability of the new URL structure, canonical correctness, orphaned old pages, internal-link breakage; Response vs Render if the platform changed.
- Always ask "what changed deliberately?" so intended changes are not reported as regressions.

**Pre-migration**
- The job flips from triage to **baselining**: document current state — indexable footprint, scores, key hint inventory, existing redirect landscape — as the post-migration reference point.
- Separate "fix before you migrate" from "don't carry this over".
- Read-only caveat: the baseline is only as fresh as the latest finished audit; recommend a crawl in Sitebulb as close to cutover as possible.

**New client onboarding**
- Lead: the state-of-the-nation read — biggest structural findings, balanced with early quick wins the consultant can bank for credibility.
- More explanation, heavier evidence: these recommendations will be challenged.

**Routine check**
- Lead: deltas first, brief, escalate only genuine movement. The governing rule is *don't manufacture drama*.

**Deadline-driven**
- The effort axis takes over: what is realistically shippable before the date. Quick wins lead; L/XL work is explicitly parked with a note, never silently dropped.
- Interacts hard with the `low_dev_availability` effort modifier — surface queue time honestly.

**International expansion**
- Gates the International section on. Lead: hreflang correctness, language/region targeting, locale duplicate content, international URL structure.
- Ask which markets and languages before pulling data.
