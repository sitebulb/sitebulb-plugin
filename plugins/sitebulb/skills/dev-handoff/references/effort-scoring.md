# Sitebulb Effort & Impact Scoring (shared)

Skill-agnostic. Turns a Sitebulb hint into an effort size (S–XL) and an indicative duration, via a small set of fix archetypes rather than per-hint scoring. The effort half is used by this skill (per-ticket estimates) and by What To Fix First (Skill 1) and Skill 6; the impact half (§ Impact weighting) is used by Skill 1/6 only — this skill keeps priority severity-mapped and does not compute impact. Other skills lift this file unchanged.

The classified catalogue lives in `references/hint-map.csv` — 358 hints, each with `url_filter_id` (the canonical join key; blank for accessibility-lane hints), default severity, archetype, owner, volume sensitivity, base size, lane, and (SEO lane) tier + section weight.

## Core principle

Effort = mechanism × owner × scaling. The issue type settles mechanism and owner. Affected-URL count raises effort **only** where the fix is genuinely per-URL manual work; for templated or global fixes one change fixes ten URLs or ten thousand for the same effort, so volume belongs on the impact axis, not the effort axis.

## The eight fix archetypes

| # | Archetype | Typical owner | Volume sensitivity | Base size |
|---|-----------|---------------|--------------------|-----------|
| 1 | Global config / directive | Dev / config-capable SEO | Flat | S |
| 2 | Template / theme edit | Developer | Flat | M |
| 3 | Redirect mapping | Dev / ops | Banded (hard) | S |
| 4 | Content & metadata authoring | Content / SEO copy | Banded (hard) | S |
| 5 | Per-instance code / markup fix | Developer | Banded (soft) | M |
| 6 | Performance / Core Web Vitals | Developer | Banded (soft) | L |
| 7 | Server / infrastructure | Dev / ops / host | Flat | L |
| 8 | Investigation / diagnosis | SEO lead | Flat | M |

Archetype 8 is the catch-all so nothing is unscored — a timeboxed diagnostic spike that routes to another archetype once the cause is known.

## Volume bands

Bands modulate **banded** archetypes only; **flat** archetypes (1, 2, 7, 8) ignore them. Each step raises size by one (S→M→L→XL). Breakpoints suit teams crawling large sites and are tunable.

**Hard-banded** (3, 4 — each item is real per-URL work): 1–25 → +0 · 26–100 → +1 · 101–500 → +2 · 500+ → +3.

**Soft-banded** (5, 6 — partial template economies): 1–100 → +0 · 101–1000 → +1 · 1000+ → +2.

Use the hint row's true `affectedUrlsCount` (shared-core rule 7), never a count of the sample URL list's rows.

## Context modifiers

Applied after the band step, netted together, then floored at S and capped at XL:

- **CMS self-serve for metadata** (e.g. WordPress + Yoast): −1 on archetypes 2 and 4.
- **Low / no developer availability:** +1 on dev-owned archetypes (2, 5, 6, 7) — real work that queues; also stretches duration (queue time, not work time).
- **Embedded / ample developer capacity:** −1 on the same archetypes.
- **Solo operator, no content team:** +1 on archetype 4.
- **Infrastructure owned by an external host:** do not resize — flag the issue blocked/external and sequence it later, since the team may not control the fix.

## Size and arithmetic

S = 1, M = 2, L = 3, XL = 4. `final size = base size + band step + net modifiers`, floored at S, capped at XL.

## Indicative durations (planning estimates, never commitments)

Present as ranges, label as estimates, invite the user or their dev lead to override before any is treated as a date.

- **S** — an hour or two
- **M** — half a day to a day
- **L** — 1–3 days
- **XL** — a week or more, effectively its own workstream

(Recalibrated 10 Jul 2026 after live review — the original ranges failed the sniff test on real hints. Always pair a duration with what the work actually is; a bare number reads as inflated or arbitrary.)

Where low-developer-availability is active, durations stretch and the output should say so.

## Procedure: hint → effort

This logic is **executed by `scripts/score_effort.py`, not by hand** — the title/URL join, banding, modifier netting and floor/cap are deterministic and the model slips on them. The sections above are the authoritative spec the script implements; if they ever disagree, the doc wins and the script is the bug. The script reads `hint-effort-map.csv` itself, so the 369-row catalogue never needs to enter context.

**Run it:**

```bash
echo '{"modifiers":["cms_self_serve_metadata"],
       "hints":[{"title":"<exact hint title>",
                 "affected_urls":<the hint row's affectedUrlsCount>,
                 "learn_more_url":"<hint learnMoreUrl, optional>"}]}' \
  | python3 scripts/score_effort.py
```

**The model gathers the inputs the script can't:**

1. Each hint from the audit's per-category triggered-hint lists (currently `audit_hint_category_list` → `audit_hint_list`; lost & found via `audit_lostfound_hint_list`) — resolve to the live tools per shared-core § Tool binding. Each row gives a `title`, a knowledge-base link (`learnMoreUrl`), a snake_case filter id (`urlFilterId`), and the true count (`affectedUrlsCount`).
2. The true affected-URL count — the hint row's `affectedUrlsCount` (shared-core rule 7); the sample URL list is capped at 50, so never count its rows.
3. Which context modifiers the conversation has actually surfaced (see the consuming skill for whether modifiers are asked for or only applied when already known). Vocabulary: `cms_self_serve_metadata`, `low_dev_availability`, `ample_dev_capacity`, `solo_no_content_team`, `host_managed_infra`.

**The script returns**, per hint: `archetype`, `owner`, `base_size`, `band_step`, `modifiers_applied`, final `size` (S–XL), `duration`, a ready-to-use `basis` line, the hint's `learnMoreUrl`/`section`/`section_ui`/`seo_tier`/`section_weight`/`lane` — and, when the impact inputs (`severity`, `coverage`, `indexable_urls`, `affected_urls`) are supplied, the computed `impact` with its `impact_basis`, `effective_coverage`, `traffic_multiplier`, `gated_off` and `must_fix`; plus a run `summary` with `matched`/`unmapped` counts, `gates_on`, `impact_scored`, `must_fix`, `gated_off` lists and `drift_warning`. Effort-only input (no coverage) remains valid — dev-handoff's call shape still works unchanged. A hint returned `matched: false` is unmapped — omit its effort block, never guess. The join is by `url_filter_id` first — the canonical, rename-proof key (methodology §12); pass it straight off the hint row. Normalised title is the fallback, then a *unique* `learnMoreUrl` (`matched_via: "url"`), which rescues a mapping when a hint title was renamed but its KB URL held.

**Worked examples** (these double as the script's tests in `scripts/test_score_effort.py`):
- *Has an anchored image with no alt text, 253 URLs.* A4 content authoring, hard-banded, base S → 101–500 band (+2) → **L** (~3–5 days). CMS bulk-alt self-serve (−1) → M.
- *Broken internal URLs, ~60 URLs.* A3 redirect mapping, hard-banded, base S → 26–100 (+1) → **M**.
- *Flat canonical hint, any URL count.* Global config / template edit, flat → no band → base size. The volume lands on the impact axis instead.

## Impact weighting (What To Fix First / Technical SEO Audit — not used for per-ticket effort)

Sitebulb Importance is calibrated *within* a section, so a "High" is not comparable across sections. The impact axis corrects this with a flat section-relevance multiplier on the severity term (carried in the map's `seo_tier` / `section_weight` columns):

- Tier 1 — core ranking gates (×1.0): Indexability, On Page, Duplicate Content, Redirects.
- Tier 2 — strong, some conditional (×0.7): Links, Internal URLs, XML Sitemaps, International*, Rendered*.
- Tier 3 — supporting / UX (×0.4): Mobile Friendly, Performance, AMP*.
- Tier 4 — best practice / low direct SEO (×0.2): Security.

**The locked formula** (decided 23 Jun 2026, all terms computed by `score_effort.py`):

`impact = effective section weight × severity × effective coverage × traffic linkage`

- **Severity** — geometric: Critical 8 / High 4 / Medium 2 / Low 1. `severity: none` rows are noise-filtered upstream and never score. The live hint row's severity wins; the map's `severity_default` is the fallback.
- **Effective coverage** — `coverage × (indexableUrlsCount / affectedUrlsCount)`, all three straight off the hint row. Coverage normalises by site size (a 117k-URL Low templating issue no longer swamps a 50-URL Critical); the indexable share only ever discounts, so an issue confined to non-indexable URLs falls to 0 on the impact axis — the right behaviour for an organic-search score — while its effort band still uses the full affected count, so the work lands in the low-impact quadrant rather than hiding. Two absence cases (shared-core rule 9 — the split is per-hint-type by design): a hint type that doesn't carry the split returns 0/0 against a non-zero count, and the scorer holds the share at 1.0 flagged `indexable_split_unmeasured`; **duplicate-content hints are only ever run on indexable URLs**, so their 0/0 means wholly indexable — the scorer treats their share as an exact 1.0, flagged `all_indexable_by_design`.
- **Traffic linkage** — bounded enrichment. ×1 (neutral) when no GA/GSC is attached to the audit; where it is, the consuming skill fetches a capped per-URL sample (~10–15 URLs) for only the top-ranked hints and passes summed GSC clicks (`traffic_clicks`; GA sessions as `traffic_sessions` fallback). The script applies `1 + log10(1 + clicks)`. The long tail stays neutral — the skill never requires the GA/GSC connection, it sharpens with it.
- **Conditional-section gating** — International, Rendered and AMP weight to 0 unless the run's `gates` switch them on (the context layer decides: Rendered for ecommerce/marketplace or evident JS-framework usage; International for the international-expansion situation or evident multi-locale usage; AMP on evident AMP usage). Gated-off hints are returned flagged `gated_off`, never silently dropped.
- **Homepage must-fix pin** — a Critical or High hint with `homepage_affected: true` (site root, `Depth == 0`, detected during the same bounded per-URL fetch) returns `must_fix: true` and is pinned above the matrix regardless of its computed impact. Medium/Low on the homepage stays where the score puts it.

Weight is flat, so it compounds with traffic linkage rather than yielding to it. Per-hint overrides bump cross-cutting SEO-critical hints (HTTPS/mixed content, broken internal URLs) above their section — flagged in the map. All values are editorial defaults, tunable in the workbook's Impact Weighting sheet; regenerate `hint-map.csv` from the workbook after tuning.

**Context reframing never touches these numbers.** Scores are pure; the consuming skill's emphasis rules (in What To Fix First, `references/context-emphasis.md`) select what leads and what is demoted *after* scoring.

## Known limitation

URL count is a poor proxy for *template* count, so archetypes 1 and 2 are flat by design. The MCP exposes no page-type/template grouping, so a single template fix touching 5,000 URLs is not inflated by volume — a conscious launch approximation, and the first candidate for refinement if grouping becomes available.
