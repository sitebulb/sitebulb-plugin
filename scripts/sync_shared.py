#!/usr/bin/env python3
"""Sync the canonical shared engine files from shared/ into each skill.

The five skills ship self-contained copies of the shared Sitebulb engine
(data-handling rules, effort-scoring spec, hint catalogue, scorer) so a
skill folder can be distributed standalone. The canonical source is
shared/; this script keeps the copies exact.

Usage:
    python3 scripts/sync_shared.py           # copy shared/ files into skills
    python3 scripts/sync_shared.py --check   # exit 1 if any copy drifts

Edit files in shared/ only — never a skill's copy. CI runs --check.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILLS = ROOT / "plugins" / "sitebulb" / "skills"

REFERENCES_ALL = [
    "shared-core.md",
    "context-emphasis.md",
    "effort-scoring.md",
    "hint-map.csv",
]
SCRIPTS_ALL = ["score_effort.py", "test_score_effort.py"]

# Which shared files each skill consumes. Skill-local files
# (document-template.md, pm-tool-mapping.md) are never touched.
MANIFEST: dict[str, dict[str, list[str]]] = {
    "what-to-fix-first": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "what-changed": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "technical-seo-audit": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "dev-handoff": {
        "references": ["shared-core.md", "effort-scoring.md", "hint-map.csv"],
        "scripts": SCRIPTS_ALL,
    },
    "release-check": {"references": ["shared-core.md"], "scripts": []},
}


def pairs():
    for skill, groups in MANIFEST.items():
        for subdir, names in groups.items():
            for name in names:
                yield SHARED / subdir / name, SKILLS / skill / subdir / name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="report drift instead of copying; exit 1 if any copy differs",
    )
    args = parser.parse_args()

    missing = [str(src) for src, _ in pairs() if not src.is_file()]
    if missing:
        print("Missing canonical files under shared/:", *missing, sep="\n  ")
        return 1

    drifted: list[Path] = []
    for src, dst in pairs():
        in_sync = dst.is_file() and filecmp.cmp(src, dst, shallow=False)
        if args.check:
            if not in_sync:
                drifted.append(dst)
        elif not in_sync:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"synced {dst.relative_to(ROOT)}")

    if args.check:
        if drifted:
            print("Out of sync with shared/ (edit shared/ and run sync_shared.py):")
            for path in drifted:
                print(f"  {path.relative_to(ROOT)}")
            return 1
        print("All skill copies in sync with shared/.")
    else:
        print("Sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
