#!/usr/bin/env python3
"""
Unit tests for score_effort.py. Pure, deterministic, no MCP needed — this is the
'bulletproof' half. Ground truth = the worked examples in effort-scoring.md plus
structural rules that must hold for every row. Run: python3 scripts/test_score_effort.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "score_effort.py"
MAP = HERE.parent / "references" / "hint-map.csv"

sys.path.insert(0, str(HERE))
import score_effort as se  # noqa: E402

BY_TITLE, BY_URL, BY_FILTER_ID = se.load_map(MAP)

passed = failed = 0


def check(name, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {name}\n        got:  {got!r}\n        want: {want!r}")


def score(hints, modifiers=None, gates=None):
    return se.score({"hints": hints, "modifiers": modifiers or [], "gates": gates or {}},
                    BY_TITLE, BY_URL, BY_FILTER_ID)


# --- worked examples from effort-scoring.md (the contract) -----------------

r = score([{"title": "Has an anchored image with no alt text", "affected_urls": 253}])["results"][0]
check("alt-text 253 -> L", r["size"], "L")
check("alt-text 253 -> ~1-3 days", r["duration"], "1-3 days")
check("alt-text archetype 4", r["archetype_num"], 4)
check("alt-text matched by title", r["matched_via"], "title")

r = score([{"title": "Has an anchored image with no alt text", "affected_urls": 253}],
          ["cms_self_serve_metadata"])["results"][0]
check("alt-text 253 + CMS self-serve -> M", r["size"], "M")

r = score([{"title": "Broken internal URLs", "affected_urls": 60}])["results"][0]
check("broken internal 60 -> M", r["size"], "M")
check("broken internal archetype 3", r["archetype_num"], 3)

# Flat archetype ignores volume: a flat canonical at any count stays at its base.
r = score([{"title": "Canonical contains invalid HTML attributes", "affected_urls": 99999}])["results"][0]
check("flat canonical huge count -> M (base, no band)", r["size"], "M")
check("flat canonical band_step 0", r["band_step"], 0)

# Soft-banded archetype 5: 50 -> base, 500 -> +1.
r = score([{"title": "Canonical points to a URL that is Not Found 404", "affected_urls": 50}])["results"][0]
check("soft-banded 50 -> M", r["size"], "M")
r = score([{"title": "Canonical points to a URL that is Not Found 404", "affected_urls": 500}])["results"][0]
check("soft-banded 500 -> L (+1)", r["size"], "L")


# --- structural rules that must hold for representative rows ---------------

def first_row_with(arch=None, vol=None):
    for k, row in BY_TITLE.items():
        if arch is not None and int(row["archetype_num"]) != arch:
            continue
        if vol is not None and row["volume_sensitivity"].strip().lower() != vol:
            continue
        return row["hint_title"]
    raise AssertionError("no matching row")

# Archetype 1 (global config): flat, base S -> S at any count.
t1 = first_row_with(arch=1)
r = score([{"title": t1, "affected_urls": 4000}])["results"][0]
check(f"arch1 flat -> base S ({t1[:30]})", (r["size"], r["band_step"]), ("S", 0))

# Archetype 7 (infra) with host-managed infra: flagged external, not resized.
t7 = first_row_with(arch=7)
r = score([{"title": t7, "affected_urls": 200}], ["host_managed_infra"])["results"][0]
check(f"arch7 host-managed -> external_blocked ({t7[:24]})", r["external_blocked"], True)
check("arch7 host-managed -> base L unchanged", r["size"], "L")

# low_dev_availability on a dev-owned soft-banded hint: +1 and a stretch note.
r = score([{"title": "Canonical points to a URL that is Not Found 404", "affected_urls": 50}],
          ["low_dev_availability"])["results"][0]
check("low-dev arch5 -> +1 (M->L)", r["size"], "L")
check("low-dev -> duration stretched", "stretched" in r["duration"], True)

# Floor/cap: nothing drops below S or rises above XL.
r = score([{"title": "Has an anchored image with no alt text", "affected_urls": 1},
           {"title": "Has an anchored image with no alt text", "affected_urls": 1}],
          ["cms_self_serve_metadata", "solo_no_content_team"])["results"][0]
check("floor at S (S base, net cancels/clamps)", r["size_int"] >= 1, True)


# --- join robustness -------------------------------------------------------

# Unmapped title with no usable URL -> not matched, no guess.
r = score([{"title": "Totally invented hint that does not exist"}])["results"][0]
check("bogus title -> unmapped", r["matched"], False)

# URL fallback: wrong/renamed title but a correct UNIQUE learn-more URL recovers it.
real = BY_TITLE["has an anchored image with no alt text"]
r = score([{"title": "Renamed by Gareth in v9", "affected_urls": 253,
            "learn_more_url": real["learn_more_url"]}])["results"][0]
check("renamed title + unique URL -> matched via url", (r["matched"], r["matched_via"]), (True, "url"))

# Drift signal: mostly-unmapped batch trips the warning; a clean batch does not.
s = score([{"title": "nope one"}, {"title": "nope two"}, {"title": "nope three"},
           {"title": "Broken internal URLs", "affected_urls": 10}])["summary"]
check("drift warning fires on mostly-unmapped batch", s["drift_warning"], True)
s = score([{"title": "Broken internal URLs", "affected_urls": 10}])["summary"]
check("drift warning quiet on a clean single", s["drift_warning"], False)


# --- impact axis (locked 23 Jun 2026: weight x severity x effective coverage
# --- x traffic linkage; homepage must-fix pin; conditional gating) ----------

def impact_hint(**kw):
    base = {"title": "Broken internal URLs", "affected_urls": 100,
            "indexable_urls": 100, "coverage": 10.0, "severity": "High"}
    base.update(kw)
    return base

# Effort-only call shape (no coverage/indexable) stays valid: no impact key.
r = score([{"title": "Broken internal URLs", "affected_urls": 60}])["results"][0]
check("effort-only input -> no impact key", "impact" in r, False)

# Severity scale 8/4/2/1 on identical volume terms.
imps = {}
for sev in ("Critical", "High", "Medium", "Low"):
    imps[sev] = score([impact_hint(severity=sev)])["results"][0]["impact"]
check("severity ratio Critical:Low = 8", round(imps["Critical"] / imps["Low"], 6), 8.0)
check("severity ratio High:Medium = 2", round(imps["High"] / imps["Medium"], 6), 2.0)

# Effective coverage: indexable share discounts; non-indexable-only -> 0.
full = score([impact_hint(indexable_urls=100)])["results"][0]["impact"]
half = score([impact_hint(indexable_urls=50)])["results"][0]["impact"]
none = score([impact_hint(indexable_urls=0)])["results"][0]["impact"]
check("half-indexable set halves impact", round(half / full, 6), 0.5)
check("non-indexable-only issue -> impact 0", none, 0.0)
# Explicit split: 0 indexable of a measured split -> 0; unmeasured split
# (both counts zero against non-zero affected) -> share held at 1.0, flagged.
r = score([impact_hint(indexable_urls=0, not_indexable_urls=100)])["results"][0]
check("measured zero-indexable split -> impact 0", r["impact"], 0.0)
r = score([impact_hint(indexable_urls=0, not_indexable_urls=0)])["results"][0]
check("unmeasured split -> share 1.0, flagged",
      (r["indexable_share"], r["indexable_split_unmeasured"], r["impact"] > 0),
      (1.0, True, True))
# Duplicate-content hints only run against indexable URLs, so 0/0 means the
# affected set is WHOLLY indexable: exact share 1.0, not the unmeasured fallback.
r = score([{"title": "URLs with duplicate page titles", "affected_urls": 34393,
            "indexable_urls": 0, "not_indexable_urls": 0,
            "coverage": 15.64, "severity": "High"}])["results"][0]
check("dup-content 0/0 -> all indexable by design",
      (r["indexable_share"], r["all_indexable_by_design"], r["indexable_split_unmeasured"]),
      (1.0, True, False))

# Traffic linkage: 1 + log10(1 + clicks); 999 clicks -> x4; absent -> x1.
r0 = score([impact_hint()])["results"][0]
r999 = score([impact_hint(traffic_clicks=999)])["results"][0]
check("no traffic data -> neutral x1", r0["traffic_multiplier"], 1.0)
check("999 clicks -> multiplier 4.0", r999["traffic_multiplier"], 4.0)
check("999 clicks quadruples impact", round(r999["impact"] / r0["impact"], 6), 4.0)
rga = score([impact_hint(traffic_sessions=99)])["results"][0]
check("GA sessions fallback -> x3", rga["traffic_multiplier"], 3.0)

# Conditional gating: an International hint scores 0 unless gated on.
intl_title = next(row["hint_title"] for row in BY_TITLE.values()
                  if row["section"].lower() == "international" and row["severity_default"])
gi = {"title": intl_title, "affected_urls": 40, "indexable_urls": 40,
      "coverage": 4.0, "severity": "High"}
r_off = score([gi])["results"][0]
r_on = score([gi], gates={"International": True})["results"][0]
check("International gated off -> impact 0", (r_off["impact"], r_off["gated_off"]), (0.0, True))
check("International gated on -> scores", (r_on["impact"] > 0, r_on["gated_off"]), (True, False))

# Homepage must-fix pin: Critical/High on the homepage pins; Medium does not.
r = score([impact_hint(severity="Critical", homepage_affected=True)])["results"][0]
check("Critical + homepage -> must_fix", r["must_fix"], True)
r = score([impact_hint(severity="Medium", homepage_affected=True)])["results"][0]
check("Medium + homepage -> not pinned", r["must_fix"], False)

# urlFilterId join is canonical: wrong title + right id still matches.
fid_row = BY_TITLE["broken internal urls"]
r = score([{"title": "Renamed beyond recognition", "affected_urls": 60,
            "url_filter_id": fid_row["url_filter_id"]}])["results"][0]
check("urlFilterId join beats renamed title",
      (r["matched"], r["matched_via"], r["title_key"]),
      (True, "url_filter_id", "broken internal urls"))

# Scores are context-pure: emphasis gates aside, reframing never enters here —
# same inputs, same score, regardless of business type (no such parameter exists).
a = score([impact_hint()])["results"][0]["impact"]
b = score([impact_hint()])["results"][0]["impact"]
check("determinism: identical inputs, identical impact", a, b)


# --- the CLI actually runs and emits valid JSON ----------------------------

proc = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input='{"hints":[{"title":"Broken internal URLs","affected_urls":60}]}',
    capture_output=True, text=True)
check("CLI exit 0", proc.returncode, 0)
out = json.loads(proc.stdout)
check("CLI scores via stdin -> M", out["results"][0]["size"], "M")


print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
