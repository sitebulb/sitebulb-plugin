#!/usr/bin/env python3
"""Change fragments: one file in changes/ for each change that a release ships.

A fragment is changes/<YYYY-MM-DD>-<slug>.<kind>.md. Its text is one or more
sentences for the changelog. changes/README.md is the only other file there. `scripts/release.py prepare` moves every fragment
into a new CHANGELOG.md section and into the Codex release notes, then deletes
the fragments. So changes/ holds only the changes that no release has shipped.

Usage:
    python3 scripts/changes.py new --kind fixed --message "Corrected the ..."
    python3 scripts/changes.py check                 # validate the fragments
    python3 scripts/changes.py check --base <commit> # also require a new
                                                     # fragment since <commit>

A diff needs no new fragment when it changes only CHANGELOG.md, deletes
fragments, and changes only the version and release-notes fields of the
version files. That is the diff that `release.py prepare` makes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("added", "changed", "fixed", "removed", "security", "docs", "maintenance")
NAME = re.compile(r"(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.(" + "|".join(KINDS) + r")\.md")


class ChangeError(Exception):
    pass


def iso_date(value: str) -> dt.date:
    try:
        date = dt.date.fromisoformat(value)
    except ValueError:
        date = None
    if date is None or date.isoformat() != value:
        raise ChangeError(f"{value!r} is not a YYYY-MM-DD date")
    return date


def is_fragment_path(rel: str) -> bool:
    parts = rel.split("/")
    return len(parts) == 2 and parts[0] == "changes" and NAME.fullmatch(parts[1]) is not None


def entries(root: Path) -> list[tuple[str, str, str]]:
    """Return (kind, file name, text) for each fragment, in changelog order."""
    directory = root / "changes"
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.iterdir()):
        if path.name == "README.md":
            continue
        match = NAME.fullmatch(path.name)
        if not match or path.is_symlink() or not path.is_file():
            raise ChangeError(f"changes/{path.name} is not a fragment: use "
                              f"changes/YYYY-MM-DD-<slug>.<kind>.md, kind one of {', '.join(KINDS)}")
        iso_date(match[1])
        text = path.read_text(encoding="utf-8").strip()
        if not text or "\x00" in text:
            raise ChangeError(f"changes/{path.name} is empty or holds a null byte")
        result.append((match[3], path.name, text))
    return sorted(result, key=lambda e: (KINDS.index(e[0]), e[1]))


def git(root: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if proc.returncode:
        raise ChangeError(proc.stderr.decode("utf-8", "replace").strip())
    return proc.stdout


def diff_paths(root: Path, base: str, status: str | None = None) -> list[str]:
    args = ["diff", "--no-renames", "--name-only", "-z"]
    if status:
        args.append(f"--diff-filter={status}")
    out = git(root, *args, f"{base}^{{commit}}", "HEAD", "--")
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def strip_release_fields(data, version_keys: list[tuple[str, ...]]):
    """Remove the version fields and the release notes, for comparison."""
    for keys in version_keys:
        node = data
        for key in keys[:-1]:
            node = node.get(key, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict):
            node.pop(keys[-1], None)
    publication = data.get("extensions", {}).get("com.openai", {}).get("publication", {})
    if isinstance(publication, dict):
        publication.pop("release_notes", None)
    return data


def release_only(root: Path, base: str, rel: str, version_fields: dict[str, list]) -> bool:
    """True when rel differs from base only in its version and release-notes fields."""
    if rel not in version_fields:
        return False
    try:
        before = json.loads(git(root, "show", f"{base}:{rel}"))
        after = json.loads(git(root, "show", f"HEAD:{rel}"))
    except (ChangeError, ValueError):
        return False
    keys = version_fields[rel]
    return strip_release_fields(before, keys) == strip_release_fields(after, keys)


def check(root: Path, base: str | None = None) -> str:
    fragments = entries(root)
    if base is None:
        return f"{len(fragments)} unreleased change fragment(s) are valid."
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from release import version_fields  # the one list of version fields

    fields: dict[str, list] = {}
    for path, keys in version_fields(root):
        fields.setdefault(path.relative_to(root).as_posix(), []).append(keys)
    changed = diff_paths(root, base)
    added = [p for p in diff_paths(root, base, "A") if is_fragment_path(p)]
    deleted = set(diff_paths(root, base, "D"))
    if not changed or added:
        return "This change adds a change fragment." if added else "No files changed."
    exempt = [p for p in changed
              if p == "CHANGELOG.md"
              or (p in deleted and is_fragment_path(p))
              or release_only(root, base, p, fields)]
    if len(exempt) == len(changed):
        return "No fragment needed: the diff changes only CHANGELOG.md or the release fields."
    raise ChangeError("this change needs a new fragment in changes/: run "
                      "python3 scripts/changes.py new --kind <kind> --message \"...\"")


def new(root: Path, kind: str, message: str, date: dt.date, slug: str | None) -> Path:
    message = message.strip()
    if not message or "\x00" in message:
        raise ChangeError("the message is empty or holds a null byte")
    entries(root)
    slug = slug or re.sub(r"[^a-z0-9]+", "-", message.lower()).strip("-")[:50].rstrip("-")
    path = root / "changes" / f"{date.isoformat()}-{slug}.{kind}.md"
    if not NAME.fullmatch(path.name):
        raise ChangeError(f"{path.name} is not a valid fragment name; give --slug")
    path.parent.mkdir(exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(message + "\n")
    except FileExistsError:
        raise ChangeError(f"changes/{path.name} exists; give a different --slug") from None
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("new", help="write a new fragment")
    make.add_argument("--kind", required=True, choices=KINDS)
    make.add_argument("--message", required=True)
    make.add_argument("--slug", help="file-name slug (default: from the message)")
    make.add_argument("--date", type=iso_date, help="fragment date (default: today, UTC)")
    validate = commands.add_parser("check", help="validate fragments")
    validate.add_argument("--base", help="require a new fragment in the diff from this commit to HEAD")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "new":
            date = args.date or dt.datetime.now(dt.timezone.utc).date()
            path = new(root, args.kind, args.message, date, args.slug)
            print(f"Wrote {path.relative_to(root).as_posix()}")
        else:
            print(check(root, args.base))
    except (ChangeError, OSError, UnicodeError) as error:
        print(f"changes.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
