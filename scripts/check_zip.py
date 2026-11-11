#!/usr/bin/env python3
"""Check a plugin ZIP for the items that the OpenAI plugin directory refuses.

Usage:
    python3 scripts/check_zip.py --version <X.Y.Z> [--gitleaks <path>] <zip>...

Each ZIP fails when:
- an entry path is absolute, has a backslash, an empty or `..` segment, or is
  not a regular file or a folder;
- the plugin manifest is not at the ZIP root (.codex-plugin/plugin.json);
- a manifest version is not <X.Y.Z>, or the Codex release_notes does not start
  with "<X.Y.Z>:";
- it holds an `apps` folder, a `.app.json` file, a `hooks` folder or a
  `hooks.json` file, in any letter case;
- a plugin.json at the ZIP root or in a root dot-folder (for example
  .agent-plugin/) declares `apps` or `hooks`;
- `demo_recording_url` is not an https:// URL (the CI placeholder fails here);
- gitleaks finds a secret in a file, or the ZIP holds a gitleaks
  configuration or ignore file that could turn a rule off.

Rules from https://developers.openai.com/plugins/deploy/submission,
/plugins/deploy/submission-errors and /plugins/build/plugins.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release import MANIFESTS  # noqa: E402
# "Plugin ZIP packages containing app references (apps / .app.json) or
# lifecycle hooks cannot currently be submitted." Codex finds hooks in
# hooks/hooks.json by default, or in the paths of a manifest `hooks` field.
# The names are compared in lower case.
REFUSED_FOLDERS = {"apps", "hooks"}
REFUSED_FILES = {".app.json", "hooks.json"}
REFUSED_MANIFEST_KEYS = ("apps", "hooks")
# A file that gitleaks reads from the scanned folder can turn its rules off.
GITLEAKS_FILES = {".gitleaks.toml", ".gitleaksignore"}


def entry_problems(info: zipfile.ZipInfo) -> list[str]:
    name = info.filename
    mode = info.external_attr >> 16
    problems = []
    if not name or name != name.strip() or "\\" in name or name.startswith("/"):
        problems.append(f"{name!r}: the path is empty, absolute, has outer spaces or a backslash")
    segments = name.rstrip("/").split("/")
    if any(s in ("", ".", "..") for s in segments):
        problems.append(f"{name!r}: the path has an empty, '.' or '..' segment")
    kind = stat.S_IFMT(mode)
    if kind and kind not in (stat.S_IFREG, stat.S_IFDIR):
        problems.append(f"{name!r}: the entry is not a regular file or a folder")
    return problems


def content_problems(names: list[str]) -> list[str]:
    problems = []
    for name in names:
        segments = name.lower().rstrip("/").split("/")
        folders = segments if name.endswith("/") else segments[:-1]
        for folder in sorted(REFUSED_FOLDERS.intersection(folders)):
            problems.append(f"{name}: the ZIP holds the {folder}/ folder, which OpenAI refuses")
        if not name.endswith("/") and segments[-1] in REFUSED_FILES:
            problems.append(f"{name}: OpenAI refuses a {segments[-1]} file")
        if not name.endswith("/") and segments[-1] in GITLEAKS_FILES:
            problems.append(f"{name}: a gitleaks configuration file can hide a secret from the scan")
    return problems


def is_root_manifest(name: str) -> bool:
    """plugin.json at the ZIP root or in a root dot-folder, where the portal reads manifests."""
    segments = name.lower().split("/")
    return segments[-1] == "plugin.json" and (
        len(segments) == 1 or (len(segments) == 2 and segments[0].startswith(".")))


def manifest_problems(read, names: set[str], version: str) -> list[str]:
    problems = []
    if ".codex-plugin/plugin.json" not in names:
        return [".codex-plugin/plugin.json is not at the ZIP root"]
    for rel in sorted(n for n in names if is_root_manifest(n)):
        data = json.loads(read(rel))
        if rel.split("/")[0] in MANIFESTS and data.get("version") != version:
            problems.append(f"{rel}: version is {data.get('version')!r}, expected {version!r}")
        scopes = [data, data.get("extensions", {}).get("com.openai", {})]
        for key in REFUSED_MANIFEST_KEYS:
            if any(isinstance(s, dict) and key in s for s in scopes):
                problems.append(f"{rel}: declares {key!r}, which OpenAI refuses in a directory ZIP")
    openai = json.loads(read(".codex-plugin/plugin.json")).get("extensions", {}).get("com.openai", {})
    demo = openai.get("review", {}).get("demo_recording_url")
    parts = urlsplit(demo) if isinstance(demo, str) else None
    if not (parts and parts.scheme == "https" and parts.hostname and not parts.username
            and " " not in demo):
        problems.append(f".codex-plugin/plugin.json: demo_recording_url {demo!r} is not an https:// URL")
    notes = openai.get("publication", {}).get("release_notes")
    if not (isinstance(notes, str) and notes.startswith(f"{version}:")):
        problems.append(f".codex-plugin/plugin.json: release_notes does not start with '{version}:'")
    return problems


def run_gitleaks(binary: str, folder: Path, tmp: Path, env) -> tuple[list[dict], str | None]:
    """Scan folder. Return the findings, or an error text when gitleaks fails."""
    report, ignore = tmp / f"{folder.name}.json", tmp / "ignore"
    ignore.mkdir(exist_ok=True)
    proc = subprocess.run(
        [binary, "dir", "--no-banner", "--no-color", "--log-level", "warn", "--redact",
         "--ignore-gitleaks-allow", "--gitleaks-ignore-path", str(ignore), "--exit-code", "3",
         "--report-format", "json", "--report-path", str(report), str(folder)],
        capture_output=True, text=True, env=env)
    if proc.returncode not in (0, 3):
        return [], f"gitleaks failed with exit {proc.returncode}:\n{(proc.stdout + proc.stderr).strip()}"
    try:
        findings = json.loads(report.read_text(encoding="utf-8") or "[]")
    except (OSError, ValueError) as error:
        return [], f"gitleaks wrote no readable report: {error}"
    if proc.returncode == 3 and not findings:
        return [], "gitleaks reported a secret but its report holds no finding"
    return findings, None


def gitleaks_problems(archive: zipfile.ZipFile, gitleaks: str) -> list[str]:
    """Scan the ZIP two times with the default gitleaks rules.

    The first scan reads the files at their ZIP paths, so the rules that apply
    only to some paths (for example *.yaml) run. The default configuration
    also skips every path that matches its global allowlist, for example
    *.png, *.woff or node_modules/. So the second scan reads each file again
    under a name that no allowlist matches.
    """
    binary = shutil.which(gitleaks)
    if not binary:
        return [f"gitleaks is not installed at {gitleaks!r}, so the ZIP is not scanned"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS_")}
    files = [info.filename for info in archive.infolist() if not info.is_dir()]
    found: set[tuple[str, str, int]] = set()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        unpacked, flat = tmp / "unpacked", tmp / "flat"
        archive.extractall(unpacked)
        flat.mkdir()
        for number, name in enumerate(files):
            (flat / f"file{number}").write_bytes(archive.read(name))
        for folder, zip_name in ((unpacked, lambda p: Path(p).relative_to(unpacked).as_posix()),
                                 (flat, lambda p: files[int(Path(p).name[4:])])):
            findings, error = run_gitleaks(binary, folder, tmp, env)
            if error:
                return [error]
            found.update((zip_name(f["File"]), f["RuleID"], f["StartLine"]) for f in findings)
    return [f"{name}:{line}: gitleaks found a secret (rule {rule})"
            for name, rule, line in sorted(found)]


def check(path: Path, version: str, gitleaks: str) -> list[str]:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        return [f"not a readable ZIP: {error}"]
    with archive:
        infos = archive.infolist()
        if not infos:
            return ["the ZIP is empty"]
        problems = [p for info in infos for p in entry_problems(info)]
        if problems:
            return problems  # never unpack an unsafe path
        names = [i.filename for i in infos]
        problems += content_problems(names)
        try:
            problems += manifest_problems(archive.read, set(names), version)
        except (KeyError, ValueError, AttributeError) as error:
            problems.append(f"a manifest is not a valid JSON object: {error}")
        problems += gitleaks_problems(archive, gitleaks)
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="the release version, X.Y.Z")
    parser.add_argument("--gitleaks", default="gitleaks", help="the gitleaks binary")
    parser.add_argument("zips", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = False
    for path in args.zips:
        problems = check(path, args.version, args.gitleaks)
        if problems:
            failed = True
            print(f"{path.name}: FAIL", *problems, sep="\n  ")
        else:
            print(f"{path.name}: OK (no secret, apps, .app.json or hooks; https demo URL; version {args.version})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
