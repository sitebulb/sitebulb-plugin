#!/usr/bin/env python3
"""Generate the skills, licence and logo of each plugin from shared/.

The repository ships two plugins, sitebulb-desktop and sitebulb-cloud, with
the same five skills. Each plugin folder must be self-contained: the Claude
plugin directory refuses symbolic links and component paths outside the plugin
folder, Cursor refuses `..` in manifest paths, and OpenAI takes one ZIP per
plugin. So each plugin carries its own copy, and shared/ is the only source:

- shared/skills/<skill>/  the files that belong to one skill (SKILL.md,
                          README.md, skill-local references and scripts)
- shared/references/, shared/scripts/
                          the engine files that several skills use; MANIFEST
                          below says which skill gets which file
- shared/assets/logo.png  the logo of both plugins
- LICENSE                 the licence of both plugins

Everything under plugins/<plugin>/skills/, plus plugins/<plugin>/LICENSE and
plugins/<plugin>/assets/logo.png, is generated. The manifests, .mcp.json,
README.md and LISTING.md of each plugin are written by hand, because they
differ.

Usage:
    python3 scripts/sync_shared.py           # write the generated files
    python3 scripts/sync_shared.py --check   # exit 1 if a generated file
                                             # differs, is missing or is stale

Edit files in shared/ only, never a plugin's copy. CI runs --check.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILL_SOURCES = SHARED / "skills"
PLUGINS = ["sitebulb-desktop", "sitebulb-cloud"]

REFERENCES_ALL = [
    "shared-core.md",
    "context-emphasis.md",
    "effort-scoring.md",
    "hint-map.csv",
]
SCRIPTS_ALL = ["score_effort.py", "test_score_effort.py"]

# Which engine files each skill consumes. Each skill also gets every file
# under shared/skills/<skill>/.
MANIFEST: dict[str, dict[str, list[str]]] = {
    "sitebulb-what-to-fix-first": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "sitebulb-what-changed": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "sitebulb-technical-seo-audit": {"references": REFERENCES_ALL, "scripts": SCRIPTS_ALL},
    "sitebulb-dev-handoff": {
        "references": ["shared-core.md", "effort-scoring.md", "hint-map.csv"],
        "scripts": SCRIPTS_ALL,
    },
    "sitebulb-release-check": {"references": ["shared-core.md"], "scripts": []},
}

IGNORED = {"__pycache__", ".DS_Store"}


def source_files(directory: Path):
    for path in sorted(directory.rglob("*")):
        if path.is_file() and not IGNORED.intersection(path.parts) and path.suffix != ".pyc":
            yield path


def pairs():
    """Yield (source, destination) for every generated file."""
    for plugin in PLUGINS:
        dest = ROOT / "plugins" / plugin
        yield ROOT / "LICENSE", dest / "LICENSE"
        yield SHARED / "assets" / "logo.png", dest / "assets" / "logo.png"
        for skill, groups in MANIFEST.items():
            for src in source_files(SKILL_SOURCES / skill):
                yield src, dest / "skills" / skill / src.relative_to(SKILL_SOURCES / skill)
            for subdir, names in groups.items():
                for name in names:
                    yield SHARED / subdir / name, dest / "skills" / skill / subdir / name


def stale_files(expected: set[Path]):
    """Files under a plugin's generated skills/ folder that no source produces."""
    for plugin in PLUGINS:
        skills = ROOT / "plugins" / plugin / "skills"
        if skills.is_dir():
            for path in source_files(skills):
                if path not in expected:
                    yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--check", action="store_true",
        help="report differences instead of writing; exit 1 if any generated file differs",
    )
    args = parser.parse_args()

    all_pairs = list(pairs())
    unknown = sorted(set(p.name for p in SKILL_SOURCES.iterdir() if p.is_dir()) - set(MANIFEST))
    if unknown:
        print("Skill folders under shared/skills/ that MANIFEST does not list:",
              *unknown, sep="\n  ")
        return 1
    missing = sorted({str(src) for src, _ in all_pairs if not src.is_file()})
    if missing:
        print("Missing source files:", *missing, sep="\n  ")
        return 1

    expected = {dst for _, dst in all_pairs}
    drifted = [dst for src, dst in all_pairs
               if not (dst.is_file() and filecmp.cmp(src, dst, shallow=False))]
    stale = list(stale_files(expected))

    if args.check:
        if drifted or stale:
            print("Plugin files out of sync with shared/ "
                  "(edit shared/ and run python3 scripts/sync_shared.py):")
            for path in drifted:
                print(f"  differs or missing: {path.relative_to(ROOT)}")
            for path in stale:
                print(f"  not generated from shared/: {path.relative_to(ROOT)}")
            return 1
        print("All generated plugin files are in sync with shared/.")
        return 0

    for src, dst in all_pairs:
        if dst in drifted:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"synced {dst.relative_to(ROOT)}")
    for path in stale:
        path.unlink()
        print(f"removed {path.relative_to(ROOT)}")
    print("Sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
