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
- it holds an `apps` folder, a `.app.json` file, a `hooks` folder, a
  `hooks.json` file, or a manifest that declares `apps` or `hooks`;
- `demo_recording_url` is not an https:// URL (the CI placeholder fails here);
- gitleaks finds a secret in the unpacked files, or holds a gitleaks
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
        segments = name.rstrip("/").split("/")
        folders = segments if name.endswith("/") else segments[:-1]
        for folder in REFUSED_FOLDERS.intersection(folders):
            problems.append(f"{name}: the ZIP holds the {folder}/ folder, which OpenAI refuses")
        if not name.endswith("/") and segments[-1] in REFUSED_FILES:
            problems.append(f"{name}: OpenAI refuses a {segments[-1]} file")
        if not name.endswith("/") and segments[-1] in GITLEAKS_FILES:
            problems.append(f"{name}: a gitleaks configuration file can hide a secret from the scan")
    return problems


def manifest_problems(read, names: set[str], version: str) -> list[str]:
    problems = []
    if ".codex-plugin/plugin.json" not in names:
        return [".codex-plugin/plugin.json is not at the ZIP root"]
    for folder in MANIFESTS:
        rel = f"{folder}/plugin.json"
        if rel not in names:
            continue
        data = json.loads(read(rel))
        if data.get("version") != version:
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


def gitleaks_problems(archive: zipfile.ZipFile, gitleaks: str) -> list[str]:
    binary = shutil.which(gitleaks)
    if not binary:
        return [f"gitleaks is not installed at {gitleaks!r}, so the ZIP is not scanned"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS_")}
    with tempfile.TemporaryDirectory() as tmp:
        unpacked, ignore = Path(tmp) / "unpacked", Path(tmp) / "ignore"
        ignore.mkdir()
        archive.extractall(unpacked)
        proc = subprocess.run(
            [binary, "dir", "--no-banner", "--no-color", "--redact", "--verbose", "--ignore-gitleaks-allow",
             "--gitleaks-ignore-path", str(ignore), "--exit-code", "3", str(unpacked)],
            capture_output=True, text=True, env=env)
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 3:
        return [f"gitleaks found a secret:\n{output}"]
    if proc.returncode:
        return [f"gitleaks failed with exit {proc.returncode}:\n{output}"]
    return []


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
