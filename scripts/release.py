#!/usr/bin/env python3
"""Prepare, check and build a release of the Sitebulb plugins.

Usage:
    python3 scripts/release.py versions
        Print every version field. Exit 1 when two of them differ.
    python3 scripts/release.py prepare <X.Y.Z> [--date YYYY-MM-DD]
        Set every version field to X.Y.Z, move the change fragments into a new
        CHANGELOG.md section, write the same notes to publication.release_notes
        in each Codex manifest, and delete the fragments.
    python3 scripts/release.py check-tag <vX.Y.Z> [--on <ref>]
        Exit 1 when a version field is not X.Y.Z, or the tag commit is not in <ref>.
    python3 scripts/release.py build <X.Y.Z> --out <dir>
        Write <plugin>-<X.Y.Z>.zip and <plugin>-<X.Y.Z>.zip.sha256 for each plugin.
        Check each ZIP with scripts/check_zip.py before an upload.

Only the Python standard library is used, so CI and a person run the same code.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changes import ChangeError, entries, iso_date  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# The manifest folders of each plugin. Each plugin.json holds "version".
MANIFESTS = (".claude-plugin", ".codex-plugin", ".cursor-plugin")
# Marketplace files that hold a version, and the keys of that version.
MARKETPLACE_VERSIONS = ((".cursor-plugin/marketplace.json", ("metadata", "version")),)
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
# The Anthropic portal reads LISTING.md. It is not part of the plugin.
ZIP_EXCLUDE = {"LISTING.md"}
IGNORED = {"__pycache__", ".DS_Store"}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ReleaseError(Exception):
    pass


def plugin_dirs(root: Path) -> list[Path]:
    return sorted(p for p in (root / "plugins").iterdir() if p.is_dir())


def version_fields(root: Path) -> list[tuple[Path, tuple[str, ...]]]:
    """Every (file, keys) that holds the release version. The one list."""
    fields = [(plugin / m / "plugin.json", ("version",))
              for plugin in plugin_dirs(root) for m in MANIFESTS]
    fields += [(root / rel, keys) for rel, keys in MARKETPLACE_VERSIONS]
    return fields


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lookup(data, keys):
    for key in keys:
        data = data.get(key) if isinstance(data, dict) else None
    return data


def versions(root: Path) -> dict[str, object]:
    return {f"{path.relative_to(root).as_posix()}:{'.'.join(keys)}": lookup(read_json(path), keys)
            for path, keys in version_fields(root)}


def single_version(root: Path) -> str:
    found = versions(root)
    if len(set(map(str, found.values()))) != 1:
        lines = "\n  ".join(f"{k} = {v!r}" for k, v in found.items())
        raise ReleaseError(f"the version fields differ:\n  {lines}")
    return str(next(iter(found.values())))


def semver(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ReleaseError(f"{value!r} is not a version of the form X.Y.Z")
    return tuple(int(n) for n in match.groups())


def replace_value(text: str, key: str, value: str, path: Path) -> str:
    """Replace the one string value of key, and keep the rest of the file as it is."""
    pattern = re.compile(r'("' + re.escape(key) + r'"\s*:\s*)"(?:[^"\\]|\\.)*"')
    new, count = pattern.subn(lambda m: m[1] + json.dumps(value, ensure_ascii=False), text)
    if count != 1:
        raise ReleaseError(f"{path} holds {count} {key!r} fields, expected 1")
    return new


def notes(fragments) -> str:
    return " ".join(" ".join(text.split()) for _, _, text in fragments)


def changelog_section(version: str, date: dt.date, fragments) -> str:
    bullets = "".join(f"- {' '.join(text.split())}\n" for _, _, text in fragments)
    return f"## {version} — {date.isoformat()}\n\n{bullets}\n"


def prepare(root: Path, version: str, date: dt.date) -> list[str]:
    current = single_version(root)
    if semver(version) <= semver(current):
        raise ReleaseError(f"{version} is not later than the current version {current}")
    fragments = entries(root)
    if not fragments:
        raise ReleaseError("changes/ holds no fragments, so the release has no notes")
    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if not text.startswith("# Changelog\n"):
        raise ReleaseError("CHANGELOG.md does not start with '# Changelog'")
    if re.search(rf"^## {re.escape(version)}(?!\S)", text, re.M):
        raise ReleaseError(f"CHANGELOG.md already has a {version} section")
    # The newest section goes above the first version section.
    first = re.search(r"^## ", text, re.M)
    at = first.start() if first else len(text)
    release_notes = f"{version}: {notes(fragments)}"

    writes: dict[Path, str] = {changelog: text[:at] + changelog_section(version, date, fragments)
                               + text[at:]}
    for path, keys in version_fields(root):
        source = writes.get(path, path.read_text(encoding="utf-8"))
        writes[path] = replace_value(source, keys[-1], version, path)
    for plugin in plugin_dirs(root):
        path = plugin / ".codex-plugin" / "plugin.json"
        writes[path] = replace_value(writes[path], "release_notes", release_notes, path)
    for path, keys in version_fields(root):
        if lookup(json.loads(writes[path]), keys) != version:
            raise ReleaseError(f"{path} does not hold {version} after the edit")
    for path, new in writes.items():
        path.write_text(new, encoding="utf-8", newline="\n")
    for _, name, _ in fragments:
        (root / "changes" / name).unlink()
    return [name for _, name, _ in fragments]


def check_tag(root: Path, tag: str, on: str | None) -> str:
    if not tag.startswith("v"):
        raise ReleaseError(f"tag {tag!r} does not start with 'v'")
    version = tag[1:]
    semver(version)
    wrong = {k: v for k, v in versions(root).items() if v != version}
    if wrong:
        lines = "\n  ".join(f"{k} = {v!r}" for k, v in wrong.items())
        raise ReleaseError(f"tag {tag} does not agree with these version fields:\n  {lines}")
    if on:
        proc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", "HEAD", on],
                              capture_output=True, text=True)
        if proc.returncode:
            raise ReleaseError(f"the tagged commit is not in {on}: {proc.stderr.strip() or 'not an ancestor'}")
    return version


def plugin_files(plugin: Path) -> list[Path]:
    files = []
    for path in sorted(plugin.rglob("*")):
        rel = path.relative_to(plugin)
        if IGNORED.intersection(rel.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ReleaseError(f"{path} is a symbolic link; the ZIP takes regular files only")
        if path.is_file() and rel.as_posix() not in ZIP_EXCLUDE:
            files.append(path)
    return files


def build(root: Path, version: str, out: Path) -> list[Path]:
    semver(version)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for plugin in plugin_dirs(root):
        target = out / f"{plugin.name}-{version}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in plugin_files(plugin):
                # The plugin folder's contents go at the archive root.
                info = zipfile.ZipInfo(path.relative_to(plugin).as_posix(), ZIP_TIME)
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        (out / f"{target.name}.sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
        written.append(target)
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("versions", help="print the version fields; exit 1 if they differ")
    prep = commands.add_parser("prepare", help="set the version and write the release notes")
    prep.add_argument("version")
    prep.add_argument("--date", type=iso_date, help="section date (default: today, UTC)")
    tag = commands.add_parser("check-tag", help="exit 1 if the tag is not the version everywhere")
    tag.add_argument("tag")
    tag.add_argument("--on", help="also exit 1 if HEAD is not in this ref, for example origin/main")
    make = commands.add_parser("build", help="write the plugin ZIPs and their SHA-256 sums")
    make.add_argument("version")
    make.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "versions":
            for field, value in versions(root).items():
                print(f"{field} = {value}")
            print(f"Every version field is {single_version(root)}.")
        elif args.command == "prepare":
            date = args.date or dt.datetime.now(dt.timezone.utc).date()
            consumed = prepare(root, args.version, date)
            print(f"Set every version field to {args.version} and wrote the {args.version} notes "
                  f"to CHANGELOG.md and the Codex manifests. Deleted {len(consumed)} fragment(s):",
                  *(f"changes/{name}" for name in consumed), sep="\n  ")
        elif args.command == "check-tag":
            print(f"Tag {args.tag} agrees with every version field ({check_tag(root, args.tag, args.on)}).")
        else:
            for path in build(root, args.version, args.out):
                print(f"Wrote {path} and {path.name}.sha256")
    except (ReleaseError, ChangeError, OSError, ValueError) as error:
        print(f"release.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
