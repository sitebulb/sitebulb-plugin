#!/usr/bin/env python3
"""
Deterministic two-axis scorer for the Sitebulb effort/impact model (What To Fix First).

Implements BOTH halves of references/effort-scoring.md so the model does not
hand-compute either: the urlFilterId/title/URL join, volume banding, context
modifiers and floor/cap arithmetic on the effort side; and on the impact side
severity mapping (Critical 8 / High 4 / Medium 2 / Low 1), section weighting
with conditional-section gating, effective coverage
(coverage x indexable share of the affected set), the traffic-linkage
multiplier (1 + log10(1 + clicks), GA sessions fallback, x1 when absent) and
the homepage must-fix pin. The CSV catalogue is read by this script and never
needs to enter the model's context. Context reframing NEVER happens here —
scores are pure; the emphasis rules act on the output, not the arithmetic.

The model's remaining job: gather inputs (each hint row's url_filter_id,
title, severity, coverage, affectedUrlsCount and indexableUrlsCount — true
counts, never a count of sample-list rows — plus sampled traffic and the
homepage flag for top-ranked hints, gates, and which context modifiers the
conversation has surfaced) and pass them in; then use the returned values
verbatim.

Spec lives in references/effort-scoring.md — that file is authoritative; this
script is its executor. If the two ever disagree, the doc wins and this is a bug.

Usage:
    echo '{"hints":[{"title":"Has an anchored image with no alt text","affected_urls":253}]}' \
        | python3 scripts/score_effort.py
    python3 scripts/score_effort.py --input run.json --modifiers cms_self_serve_metadata

Input JSON:
    {
      "modifiers": ["cms_self_serve_metadata"],         # optional, run-level
      "hints": [
        {"title": "...", "affected_urls": 253,
         "learn_more_url": "https://sitebulb.com/hints/..."}   # url optional
      ]
    }

Output JSON: per-hint results plus a run-level summary (incl. the drift signal).
"""
from __future__ import annotations

import argparse
import math
import csv
import json
import re
import sys
from pathlib import Path

# --- locations -------------------------------------------------------------

DEFAULT_MAP = Path(__file__).resolve().parent.parent / "references" / "hint-map.csv"

# --- spec constants (mirror references/effort-scoring.md; tunable there) ----

SIZE_LETTERS = {1: "S", 2: "M", 3: "L", 4: "XL"}
SIZE_WORDS = {1: "Small", 2: "Medium", 3: "Large", 4: "XL"}
DURATIONS = {
    1: "an hour or two",
    2: "half a day to a day",
    3: "1-3 days",
    4: "a week or more (its own workstream)",
}

# Archetypes whose effort scales with affected-URL volume, and how.
HARD_BANDED = "banded (hard)"   # archetypes 3, 4 — real per-URL work
SOFT_BANDED = "banded (soft)"   # archetypes 5, 6 — partial template economies
FLAT = "flat"                   # archetypes 1, 2, 7, 8 — volume ignored

# Context modifiers: which archetypes each touches. Mirrors the doc.
KNOWN_MODIFIERS = {
    "cms_self_serve_metadata",   # -1 on archetypes 2 and 4
    "low_dev_availability",      # +1 on dev-owned 2,5,6,7; also stretches duration
    "ample_dev_capacity",        # -1 on dev-owned 2,5,6,7
    "solo_no_content_team",      # +1 on archetype 4
    "host_managed_infra",        # arch 7: do not resize, flag blocked/external
}
DEV_OWNED = {2, 5, 6, 7}

# --- impact-side constants (locked 23 Jun 2026; tunable in the workbook) -----

SEVERITY_NUM = {"critical": 8, "high": 4, "medium": 2, "low": 1}
# Sections that only count where the site uses them. Gated by the context
# layer: pass gates={"International": True, ...} to switch one ON; default OFF
# (weight -> 0). Keys are the map's machine section names.
CONDITIONAL_SECTIONS = {"international", "rendered", "amp"}

# Drift signal: if this share (or more) of a run's hints fail to map AND at least
# this many are unmapped, the catalogue is probably stale for this Sitebulb
# version — surface it rather than silently shipping tickets without estimates.
DRIFT_SHARE = 0.30
DRIFT_MIN_COUNT = 3


# --- normalisation ---------------------------------------------------------

def normalize_title(s: str) -> str:
    """Trim, collapse internal whitespace, casefold — the join key rule."""
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def normalize_url(u: str) -> str:
    """Strip ?query and #fragment, lowercase, drop trailing slash, drop scheme."""
    if not u:
        return ""
    u = u.split("#", 1)[0].split("?", 1)[0].strip().lower()
    u = re.sub(r"^https?://", "", u)
    return u.rstrip("/")


# --- catalogue -------------------------------------------------------------

def load_map(path: Path):
    """Return (by_title_key, by_url, by_filter_id) indexes. by_url maps a
    normalised URL to the set of title_keys carrying it, so we can tell unique
    URLs from shared ones. by_filter_id is the canonical join (unique per hint,
    stable across releases; blank for accessibility-lane hints)."""
    by_title: dict[str, dict] = {}
    by_url: dict[str, set] = {}
    by_filter_id: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = row["title_key"].strip()
            if not key:
                key = normalize_title(row["hint_title"])
            by_title[key] = row
            uk = normalize_url(row["learn_more_url"])
            if uk:
                by_url.setdefault(uk, set()).add(key)
            fid = (row.get("url_filter_id") or "").strip()
            if fid:
                by_filter_id[fid] = row
    return by_title, by_url, by_filter_id


# --- scoring ---------------------------------------------------------------

def hard_band(n: int) -> int:
    if n <= 25:
        return 0
    if n <= 100:
        return 1
    if n <= 500:
        return 2
    return 3


def soft_band(n: int) -> int:
    if n <= 100:
        return 0
    if n <= 1000:
        return 1
    return 2


def band_step(volume_sensitivity: str, affected_urls: int) -> int:
    v = (volume_sensitivity or "").strip().lower()
    if v == HARD_BANDED:
        return hard_band(affected_urls)
    if v == SOFT_BANDED:
        return soft_band(affected_urls)
    return 0  # flat or unknown -> no band


def base_size_int(row: dict) -> int:
    letter = (row.get("base_size") or "").strip().upper()
    inv = {v: k for k, v in SIZE_LETTERS.items()}
    if letter in inv:
        return inv[letter]
    # Fallback by archetype if a base cell is ever blank (shouldn't happen).
    arch = int(row["archetype_num"])
    return {1: 1, 2: 2, 3: 1, 4: 1, 5: 2, 6: 3, 7: 3, 8: 2}.get(arch, 2)


def apply_modifiers(arch: int, modifiers: set):
    """Return (net_delta, applied_notes, external_blocked, duration_stretch)."""
    notes, net = [], 0
    external_blocked = "host_managed_infra" in modifiers and arch == 7
    duration_stretch = False

    if "cms_self_serve_metadata" in modifiers and arch in (2, 4):
        net -= 1
        notes.append("CMS self-serve metadata: -1")
    if not external_blocked:
        if "low_dev_availability" in modifiers and arch in DEV_OWNED:
            net += 1
            duration_stretch = True
            notes.append("limited dev availability: +1")
        if "ample_dev_capacity" in modifiers and arch in DEV_OWNED:
            net -= 1
            notes.append("ample dev capacity: -1")
    if "solo_no_content_team" in modifiers and arch == 4:
        net += 1
        notes.append("solo, no content team: +1")
    if external_blocked:
        notes.append("infra host-managed: flagged blocked/external, not resized")
    return net, notes, external_blocked, duration_stretch


def clamp(n: int) -> int:
    return max(1, min(4, n))


def build_basis(row, affected_urls, vol, step, base_int, mod_notes,
                external_blocked) -> str:
    archetype = (row.get("archetype") or "").strip()
    desc = archetype[0].lower() + archetype[1:] if archetype else "fix"
    v = (vol or "").strip().lower()
    if v in (HARD_BANDED, SOFT_BANDED):
        band_word = "hard-banded" if v == HARD_BANDED else "soft-banded"
        if step > 0:
            core = (f"{desc}, {band_word}; {affected_urls} affected URLs "
                    f"add +{step} to a {SIZE_WORDS[base_int]} base")
        else:
            core = (f"{desc}, {band_word}; {affected_urls} affected URLs sit in "
                    f"the base band (no step)")
    else:
        core = f"{desc}, flat - volume lands on the impact axis, not effort"
    if mod_notes:
        core += ". " + "; ".join(mod_notes)
    return core + "."


def severity_number(sev: str):
    return SEVERITY_NUM.get((sev or "").strip().lower())


def compute_impact(hint: dict, row: dict, gates: dict) -> dict:
    """Impact = effective section weight x severity x effective coverage x
    traffic linkage. Returns {} when the impact inputs aren't supplied (the
    effort-only call shape stays valid — sitebulb-dev-handoff compatibility)."""
    has_inputs = ("coverage" in hint and "indexable_urls" in hint)
    sev = hint.get("severity") or row.get("severity_default") or ""
    sev_num = severity_number(sev)
    if not has_inputs or sev_num is None:
        # severity 'none' rows are noise-filtered upstream; no impact score.
        return {}

    section = (row.get("section") or "").strip()
    try:
        weight = float(row.get("section_weight") or 0)
    except ValueError:
        weight = 0.0
    gated_off = False
    if section.lower() in CONDITIONAL_SECTIONS:
        on = bool((gates or {}).get(section) or (gates or {}).get(section.lower()))
        if not on:
            weight, gated_off = 0.0, True

    affected = int(hint.get("affected_urls") or 0)
    indexable = int(hint.get("indexable_urls") or 0)
    coverage = float(hint.get("coverage") or 0)
    # Indexable share discounts by the indexable fraction of the affected set.
    # The split is per-hint-type by design (shared-core rule 9): types that
    # don't carry it return 0/0 against a non-zero affected count. Two cases:
    # duplicate-content hints only ever run against indexable URLs, so their
    # 0/0 means the set is WHOLLY indexable — share is an exact 1.0; for any
    # other type the share is unknown and is held at 1.0, flagged. Detection
    # needs not_indexable_urls supplied; without it, indexable is trusted.
    split_unmeasured = False
    all_indexable = False
    if "not_indexable_urls" in hint:
        not_indexable = int(hint.get("not_indexable_urls") or 0)
        if affected > 0 and indexable == 0 and not_indexable == 0:
            if (row.get("section") or "").strip().lower() == "duplicate content":
                all_indexable = True
            else:
                split_unmeasured = True
    share = 1.0 if (split_unmeasured or all_indexable) else (
        (indexable / affected) if affected > 0 else 0.0)
    eff_cov = coverage * share

    clicks = hint.get("traffic_clicks")
    sessions = hint.get("traffic_sessions")
    if clicks is not None:
        traffic = 1 + math.log10(1 + float(clicks))
        traffic_src = "gsc_clicks"
    elif sessions is not None:
        traffic = 1 + math.log10(1 + float(sessions))
        traffic_src = "ga_sessions"
    else:
        traffic, traffic_src = 1.0, "none (neutral x1)"

    impact = weight * sev_num * eff_cov * traffic
    must_fix = bool(hint.get("homepage_affected")) and sev_num >= SEVERITY_NUM["high"]

    basis = (f"weight {weight:g}" + (" (gated off)" if gated_off else "")
             + f" x severity {sev} ({sev_num})"
             + f" x effective coverage {eff_cov:.4g}"
             + (f" (coverage {coverage:g}; indexable split unmeasured, share held at 1.0)"
                if split_unmeasured else
                (f" (coverage {coverage:g}; duplicate-content checks run on indexable "
                 f"URLs only - affected set wholly indexable)")
                if all_indexable else
                f" (coverage {coverage:g} x indexable share {share:.2f})")
             + f" x traffic {traffic:.2f} ({traffic_src})")
    if must_fix:
        basis += ". Homepage affected at Critical/High: pinned must-fix above the matrix."

    return {
        "impact": round(impact, 3),
        "impact_basis": basis,
        "severity": sev,
        "severity_num": sev_num,
        "effective_coverage": round(eff_cov, 5),
        "indexable_share": round(share, 3),
        "indexable_split_unmeasured": split_unmeasured,
        "all_indexable_by_design": all_indexable,
        "traffic_multiplier": round(traffic, 3),
        "traffic_source": traffic_src,
        "gated_off": gated_off,
        "must_fix": must_fix,
    }


def score_one(hint: dict, modifiers: set, by_title, by_url, by_filter_id=None,
              gates: dict | None = None) -> dict:
    title = hint.get("title", "")
    affected = int(hint.get("affected_urls") or 0)
    url = hint.get("learn_more_url", "")

    # Join: url_filter_id is canonical (unique per hint, survives title and
    # section renames — join on it, never on hint text, per methodology §12).
    # Title is the fallback, then a UNIQUE learn-more URL — the last recovers a
    # mapping when a hint title was renamed but its knowledge-base URL held.
    key = normalize_title(title)
    matched_via = None
    row = None
    fid = (hint.get("url_filter_id") or "").strip()
    if fid and by_filter_id:
        row = by_filter_id.get(fid)
        if row is not None:
            matched_via = "url_filter_id"
    if row is None:
        row = by_title.get(key)
        if row is not None:
            matched_via = "title"
    if row is None:
        uk = normalize_url(url)
        if uk and uk in by_url and len(by_url[uk]) == 1:
            row = by_title[next(iter(by_url[uk]))]
            matched_via = "url"

    if row is None:
        return {"title": title, "affected_urls": affected, "matched": False,
                "matched_via": None,
                "note": "unmapped - omit the effort block; never guess an archetype"}

    arch = int(row["archetype_num"])
    vol = row["volume_sensitivity"]
    base_int = base_size_int(row)
    step = band_step(vol, affected)
    net, mod_notes, external_blocked, stretch = apply_modifiers(arch, modifiers)
    final = clamp(base_int + step + net)

    duration = DURATIONS[final]
    if stretch:
        duration += " (stretched by limited dev availability)"

    result = {
        "title": title,
        "title_key": row["title_key"],
        "url_filter_id": (row.get("url_filter_id") or "") or None,
        "lane": row.get("lane"),
        "section_ui": row.get("section_ui") or row.get("section"),
        "affected_urls": affected,
        "matched": True,
        "matched_via": matched_via,
        "archetype_num": arch,
        "archetype": row["archetype"],
        "owner": row["owner"],
        "volume_sensitivity": vol,
        "base_size": SIZE_LETTERS[base_int],
        "band_step": step,
        "modifiers_applied": mod_notes,
        "external_blocked": external_blocked,
        "size": SIZE_LETTERS[final],
        "size_int": final,
        "duration": duration,
        "basis": build_basis(row, affected, vol, step, base_int, mod_notes,
                             external_blocked),
        "learn_more_url": row["learn_more_url"],
        "section": row["section"],
        "seo_tier": row["seo_tier"],
        "section_weight": row.get("section_weight"),
    }
    result.update(compute_impact(hint, row, gates or {}))
    return result


def score(payload: dict, by_title, by_url, by_filter_id=None) -> dict:
    raw_mods = set(payload.get("modifiers") or [])
    unknown = sorted(raw_mods - KNOWN_MODIFIERS)
    modifiers = raw_mods & KNOWN_MODIFIERS
    gates = payload.get("gates") or {}

    results = [score_one(h, modifiers, by_title, by_url, by_filter_id, gates)
               for h in payload.get("hints", [])]
    total = len(results)
    unmapped = [r["title"] for r in results if not r["matched"]]
    drift = (len(unmapped) >= DRIFT_MIN_COUNT
             and total > 0
             and len(unmapped) / total >= DRIFT_SHARE)

    summary = {
        "total": total,
        "matched": total - len(unmapped),
        "unmapped": len(unmapped),
        "unmapped_titles": unmapped,
        "modifiers_recognised": sorted(modifiers),
        "gates_on": sorted(k for k, v in gates.items() if v),
        "impact_scored": sum(1 for r in results if "impact" in r),
        "must_fix": [r["title"] for r in results if r.get("must_fix")],
        "gated_off": [r["title"] for r in results if r.get("gated_off")],
        "drift_warning": drift,
    }
    if drift:
        summary["drift_message"] = (
            f"{len(unmapped)} of {total} hints did not map - the effort map may be "
            f"stale for this Sitebulb version. Surface this; do not silently ship "
            f"most tickets without estimates.")
    if unknown:
        summary["unknown_modifiers"] = unknown
    return {"summary": summary, "results": results}


# --- cli -------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic Sitebulb effort scorer.")
    ap.add_argument("--input", help="JSON file (default: read stdin)")
    ap.add_argument("--map", default=str(DEFAULT_MAP), help="hint-effort-map.csv path")
    ap.add_argument("--modifiers", help="comma-separated run-level modifiers "
                    "(merged with any in the JSON)")
    args = ap.parse_args(argv)

    text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    try:
        payload = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON input: {e}"}), file=sys.stderr)
        return 2
    if isinstance(payload, list):           # tolerate a bare list of hints
        payload = {"hints": payload}
    if args.modifiers:
        payload.setdefault("modifiers", [])
        payload["modifiers"] += [m.strip() for m in args.modifiers.split(",") if m.strip()]

    map_path = Path(args.map)
    if not map_path.exists():
        print(json.dumps({"error": f"catalogue not found: {map_path}"}), file=sys.stderr)
        return 2

    by_title, by_url, by_filter_id = load_map(map_path)
    print(json.dumps(score(payload, by_title, by_url, by_filter_id),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
