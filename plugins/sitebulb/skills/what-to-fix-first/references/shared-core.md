# Sitebulb MCP — Shared Data-Handling Core (v2)

Skill-agnostic rules for any skill reading the Sitebulb MCP (Desktop and Cloud are tool-for-tool identical). These encode methodology without which output quality collapses — they are not optional polish. Other Sitebulb skills reference this file unchanged. Much of the v1 guidance now lives in the MCP's own tool descriptions (render-don't-sample, honest empty states, `hasPreviousAudit`, `netChange` semantics, never invent IDs); this core keeps only what the tools don't say for themselves.

## Tool binding — resolve capabilities at runtime

The Sitebulb MCP's tool names and response field names are not a stable contract: they can be renamed or reshaped between releases, sometimes with no warning. Bind to what a tool *does*, not what it is *called*. At the start of a run, read the connected Sitebulb tools' names and descriptions and match each capability below to the tool that currently provides it. The names in parentheses are the tools as exposed at time of writing — examples to recognise, not identifiers to depend on. This is the same discipline `pm-tool-mapping.md` applies on the PM side.

**Capabilities the skill family draws on:**

- Discover projects (`project_list`; natural-language `search`). On Cloud the project list is the organisation's whole client base.
- List a project's audits and identify the latest *finished* one (`project_audit_list`).
- List an audit's hint categories (`audit_hint_category_list`) — the category is a **required** input to the hint list, so this precedes it.
- List triggered hints per category (`audit_hint_list`; a parallel pair exists for insights). Hint rows are rich: `urlFilterId` (snake_case, ready to pass on), `warningType` (issue vs opportunity), `priority`, `coverage`, `affectedUrlsCount`, `affectedUrlsChange`, previous-audit counts, and indexable/not-indexable splits. Per-hint deltas read straight off the row — lost & found is not needed for them.
- List a hint's affected-URL **sample** — up to 50 URLs, unpaginated, by design (`audit_url_list`, keyed by the row's `urlFilterId`); read one URL's column data (`audit_url_get`).
- Read report snapshots (`audit_report_list`, `audit_report_get`) — the catalogue lists only enabled reports, so every returned slug is fetchable. Two dedicated overview snapshots short-cut the catalogue: a **one-call audit overview** (`audit_report_summary`) carrying the site score with its previous value and change, priority-band counts (Critical/High/…) with deltas, and crawl-scope statistics (crawled/internal/external…) current-vs-previous; and a **one-call SEO snapshot** (`audit_report_seo`) carrying the SEO score. Both are convenience roll-ups of report data, not a new source of truth — the per-hint change list still comes from the lost & found and hint tools. On report snapshots, `hasPrevious` means comparison values are present in that snapshot; `previousAuditId` is the audit-chain pointer, and can be null even when previous values are retained (a since-deleted previous audit).
- Compare against the previous audit at hint level (`audit_lostfound_hint_list`) and, per changed hint, a URL-level sample (`audit_lostfound_url_list` — same 50-URL sample semantics).

**Preflight — run before pulling data, after the framing interview.** Resolve the specific capabilities the current skill needs against the connected tools. Each skill declares its own split:

- **No Sitebulb MCP connected at all** — stop immediately, before any interview: these skills read audit data only through the Sitebulb MCP, and there is no fallback data source. Point the user at the setup guide — https://support.sitebulb.com/en/articles/15970977-sitebulb-mcp-start-here — which covers connecting Sitebulb Desktop or Cloud from each assistant, then offer to continue once it's connected.
- **Core capability missing** — one the skill cannot produce trustworthy output without. Stop, and tell the user plainly which capability you expected, that the Sitebulb tool providing it may have been renamed or removed, and what you can see connected instead. Do not substitute another tool's data or proceed on assumption: output built on the wrong source is worse than no output, because it reads as authoritative.
- **Peripheral capability missing** — useful but not load-bearing (a traffic-data report, a knowledge-base link). Note the gap in the output and continue with what remains.

**Bind fields by role too.** Response field names (the per-row change indicator `netChange`, the knowledge-base link `learnMoreUrl`, the true-count field `affectedUrlsCount`) move for the same reasons. Describe them by what they carry, treat the current name as an example, and check the shape is what you expected before acting on it.

**Empty results are a failure signal, not an all-clear.** A filtered query that comes back empty where the hint row's count was non-zero is far more likely a wrong/renamed `urlFilterId` or a reshaped field than a clean site. Never report "no issues" off an empty result: corroborate against the hint row's `affectedUrlsCount` first, and if the two disagree, surface the discrepancy rather than the reassuring reading. (A sample *shorter* than the count is expected — samples cap at 50; the mismatch to flag is zero rows against a non-zero count.)

## Data rules

1. **Filter bookkeeping noise from lost & found.** Exclude `severity: none` and `crawl_report` rows before counting or reporting deltas. Report "two regressions, one improvement", never "138 things changed".
2. **A zero score means *not measured in this audit*, never "0/100 — critical failure".** Corroborate with triggered hints before treating a category as assessed. Likewise, a hint absent from an audit may mean its category wasn't measured, not that the issue is gone.
3. **Sanity-check crawl scope before trending or comparing.** If `crawled_urls` shifts materially between snapshots, compare ratios or call out the scope change explicitly — raw counts across different scopes mislead.
4. **Zero organic visits between non-zero snapshots is a data gap** (GA not connected for that run), never a traffic collapse.
5. **`netChange` semantics are contextual:** negative = improvement for issue hints; neutral for counter rows. Read the row type before interpreting the sign. (Now also documented in-tool; kept as a reminder.)
6. **Casing:** camelCase envelopes with snake_case `urlFilterId` throughout; history rows snake_case; `audit_url_get` columns PascalCase. Take `urlFilterId` straight from a hint/insight/lost-and-found row — no conversion step.
7. **URL lists are samples.** Cite the true `affectedUrlsCount` from the hint row — never a count of URL-list rows. Present the up-to-50-URL sample *as a sample*, and direct the user to the hint's Affected URLs export in the Sitebulb app for the full list. Never present the sample as "the list".
8. **The MCP is read-only — it cannot trigger crawls.** When users expect "crawl my site" to work, respond gracefully: "your latest finished audit is from <date>; to get fresh data, run a crawl in Sitebulb", and offer to proceed on existing data.
9. **The indexable/not-indexable split is per-hint-type, by design.** Some hint types carry the split (the two counts sum to `affectedUrlsCount`); others never do — for those the MCP currently returns both fields as 0 against a non-zero affected count, and the Sitebulb UI omits the Indexable/Not Indexable boxes entirely. Never read the 0/0 form as "none indexable". Special case: **duplicate-content hints are only ever run against indexable URLs**, so their affected set is wholly indexable by definition, even though their split fields read 0/0.
10. **Always carry each hint's `learnMoreUrl` into client-facing or dev-facing output** — the Sitebulb knowledge base is the explanation engine; don't paraphrase it away.

## Invocation framing interview

Every Sitebulb skill opens with a short framing round before pulling data. Three universal questions, tailored per skill:

1. **Output:** "Here's what this skill produces by default: <skill default>. Is that what you want, and do you want any particular branding or styling applied?"
2. **Context:** "What can you tell me about the website or business right now — e.g. has traffic tanked recently, did you just go through a major redesign or migration, is there a deadline driving this?" Context changes what the data *means* (a redesign explains a scope shift; a traffic drop reorders priorities) — fold it into interpretation, don't just note it.
3. **Role:** "Are you agency, independent consultant, or in-house?" Sets voice, framing, and who the output is for (a client, a boss, a dev team).

**Interview rules:** skip anything already answered in the conversation or evident from context; challenge non-answers ("'just a general look' — is this a client deliverable or your own triage? The output differs a lot"); one round of questions only, then proceed with stated assumptions for anything still open.
