#!/usr/bin/env python3
"""
Tests for release.py and check_zip.py. Each test runs on a git copy of this
repository in a temporary folder. The ZIP tests need gitleaks on PATH.
Run: python3 scripts/test_release.py
"""
import datetime as dt
import hashlib
import json
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import check_zip  # noqa: E402
import release  # noqa: E402

passed = failed = 0
DAY = dt.date(2026, 11, 11)
DEMO = "https://www.youtube.com/watch?v=sitebulbdemo"
PLUGINS = ["sitebulb-cloud", "sitebulb-desktop"]


def check(name, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {name}\n        got:  {got!r}\n        want: {want!r}")


def raises(name, error, func, *args):
    global passed, failed
    try:
        func(*args)
    except error:
        passed += 1
        return
    failed += 1
    print(f"  FAIL {name}: no {error.__name__}")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def copy_repo(tmp):
    """A one-commit git copy of the working tree, with no change fragments."""
    root = Path(tmp) / "repo"
    files = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others",
                            "--exclude-standard"], check=True, capture_output=True).stdout
    for rel in filter(None, files.decode("utf-8").split("\0")):
        source = REPO / rel
        # dist/ holds the ZIPs of a local build, not repository files.
        if source.is_file() and not rel.startswith("dist/"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, root / rel)
    for path in (root / "changes").glob("*.md"):
        if path.name != "README.md":
            path.unlink()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Release tests")
    git(root, "config", "user.email", "tests@example.invalid")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    return root


def fragment(root, name, text):
    (root / "changes").mkdir(exist_ok=True)
    (root / "changes" / name).write_text(text + "\n", encoding="utf-8")


def codex(root, plugin):
    return root / "plugins" / plugin / ".codex-plugin" / "plugin.json"


def edit_json(path, change):
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_demo(root, url):
    for plugin in PLUGINS:
        edit_json(codex(root, plugin), lambda d: d["extensions"]["com.openai"]["review"]
                  .__setitem__("demo_recording_url", url))


def ci_step(name):
    """The Python heredoc of one ci.yml step, so the test runs what CI runs."""
    text = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    step = text[text.index(f"- name: {name}"):]
    body = re.search(r"python3 - <<'PY'\n(.*?)\n\s*PY\n", step, re.S)[1]
    return textwrap.dedent(body)


def run_ci_step(root, name):
    return subprocess.run([sys.executable, "-"], input=ci_step(name), cwd=root,
                          capture_output=True, text=True)


# --- the version list -----------------------------------------------------------

found = release.versions(REPO)
check("seven version fields: three manifests per plugin and the Cursor marketplace",
      len(found), 7)
check("the Cursor marketplace version is in the list",
      ".cursor-plugin/marketplace.json:metadata.version" in found, True)
on_disk = {f"{p.relative_to(REPO).as_posix()}:version"
           for p in REPO.rglob("plugin.json") if ".git" not in p.parts}
check("every plugin.json in the repository is in the list", on_disk <= set(found), True)

# --- prepare --------------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    old_log = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    raises("prepare refuses an empty changes/", release.ReleaseError, release.prepare, root, "1.1.0", DAY)
    fragment(root, "2026-11-10-zip.added.md", "Added the release ZIPs.")
    fragment(root, "2026-11-11-typo.fixed.md", "Fixed a typo\nin the README.")
    raises("prepare refuses the current version", release.ReleaseError, release.prepare, root, "1.0.0", DAY)
    raises("prepare refuses an earlier version", release.ReleaseError, release.prepare, root, "0.9.0", DAY)
    raises("prepare refuses a version that is not X.Y.Z", release.ReleaseError,
           release.prepare, root, "v1.1.0", DAY)

    consumed = release.prepare(root, "1.1.0", DAY)
    check("prepare consumes both fragments", len(consumed), 2)
    check("prepare deletes the fragments", sorted(p.name for p in (root / "changes").iterdir()),
          ["README.md"])
    check("every version field is 1.1.0", set(release.versions(root).values()), {"1.1.0"})
    log = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    check("the new section is first, in the existing heading style",
          log.startswith("# Changelog\n\n## 1.1.0 — 2026-11-11\n\n"
                         "- Added the release ZIPs.\n- Fixed a typo in the README.\n\n## 1.0.0 — "), True)
    check("the earlier sections are unchanged", log.endswith(old_log.split("\n\n", 1)[1]), True)
    want = "1.1.0: Added the release ZIPs. Fixed a typo in the README."
    for plugin in PLUGINS:
        notes = json.loads(codex(root, plugin).read_text())["extensions"]["com.openai"]["publication"]
        check(f"{plugin} release_notes", notes["release_notes"], want)
    diff = git(root, "diff", "--numstat", "--", "plugins", ".cursor-plugin")
    lines = sorted(line.split("\t")[:2] for line in diff.splitlines())
    check("prepare changes one line in each version file, two in each Codex manifest",
          [l for l in lines], [["1", "1"]] * 5 + [["2", "2"]] * 2)
    for step in ("OpenAI listing and review metadata meet the submission rules",
                 "Each plugin declares its one MCP server and is listed everywhere"):
        proc = run_ci_step(root, step)
        check(f"CI step passes after prepare: {step}", (proc.returncode, proc.stdout[-60:]),
              (0, proc.stdout[-60:]))
    fragment(root, "2026-11-12-more.changed.md", "More.")
    raises("prepare refuses a version that CHANGELOG.md already has", release.ReleaseError,
           release.prepare, root, "1.1.0", DAY)

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    fragment(root, "2026-11-11-a.added.md", "A.")
    path = root / "plugins/sitebulb-desktop/.cursor-plugin/plugin.json"
    path.write_text(path.read_text().replace('"1.0.0"', '"1.0.1"'))
    raises("prepare refuses version fields that differ", release.ReleaseError,
           release.prepare, root, "1.1.0", DAY)
    check("a refused prepare keeps the fragment", (root / "changes/2026-11-11-a.added.md").exists(), True)

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    fragment(root, "2026-11-11-a-multi.changed.md",
             "- Added X.\n- Fixed Y,\n  which was broken.\n\nSecond paragraph\nover two lines.")
    fragment(root, "2026-11-11-b-list.changed.md",
             "The check now refuses:\n\n- an apps folder\n- a hooks file")
    release.prepare(root, "1.1.0", DAY)
    log = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    check("a multi-line fragment keeps one bullet for each paragraph and list item",
          log.split("## 1.0.0")[0],
          "# Changelog\n\n## 1.1.0 — 2026-11-11\n\n- Added X.\n- Fixed Y, which was broken.\n"
          "- Second paragraph over two lines.\n- The check now refuses:\n  - an apps folder\n"
          "  - a hooks file\n\n")
    notes = json.loads(codex(root, "sitebulb-desktop").read_text())["extensions"]["com.openai"]
    check("the release notes of a multi-line fragment are plain sentences",
          notes["publication"]["release_notes"],
          "1.1.0: Added X. Fixed Y, which was broken. Second paragraph over two lines. "
          "The check now refuses: an apps folder, a hooks file.")

for script, args in (("release.py", ["prepare", "1.1.0", "--date", "2026-13-01"]),
                     ("changes.py", ["new", "--kind", "docs", "--message", "x", "--date", "2026-13-01"])):
    proc = subprocess.run([sys.executable, str(HERE / script), *args], capture_output=True, text=True)
    check(f"{script} --date 2026-13-01 is a usage error, exit 2", proc.returncode, 2)
    check(f"{script} --date 2026-13-01 prints no traceback",
          ("Traceback" in proc.stderr, "is not a YYYY-MM-DD date" in proc.stderr), (False, True))

# --- check-tag ------------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    check("v1.0.0 agrees", release.check_tag(root, "v1.0.0", "main"), "1.0.0")
    raises("v1.0.1 fails", release.ReleaseError, release.check_tag, root, "v1.0.1", None)
    raises("a tag with no v fails", release.ReleaseError, release.check_tag, root, "1.0.0", None)
    # Sabotage: one manifest is left behind.
    path = root / ".cursor-plugin/marketplace.json"
    path.write_text(path.read_text().replace('"1.0.0"', '"0.9.0"'))
    raises("a tag that one version field does not hold fails", release.ReleaseError,
           release.check_tag, root, "v1.0.0", None)
    git(root, "checkout", "-q", "-b", "topic")
    git(root, "commit", "-qam", "topic")
    path.write_text(path.read_text().replace('"0.9.0"', '"1.0.0"'))
    git(root, "commit", "-qam", "topic 2")
    raises("a tag on a commit that is not in main fails", release.ReleaseError,
           release.check_tag, root, "v1.0.0", "main")
    proc = subprocess.run([sys.executable, str(HERE / "release.py"), "--root", str(root),
                           "check-tag", "v2.0.0"], capture_output=True, text=True)
    check("CLI check-tag exit 1 on a wrong tag", proc.returncode, 1)

# --- build and check_zip ----------------------------------------------------------


def secret():
    alphabet = string.ascii_letters + string.digits
    return "ghp_" + "".join(secrets.choice(alphabet) for _ in range(36))


def zip_problems(root, out, plugin="sitebulb-desktop", version="1.0.0"):
    release.build(root, version, out)
    return check_zip.check(out / f"{plugin}-{version}.zip", version, "gitleaks")


def sabotage(label, change, expect):
    """Break the guarded thing in a fresh copy and expect check_zip to say so."""
    with tempfile.TemporaryDirectory() as tmp:
        root = copy_repo(tmp)
        set_demo(root, DEMO)
        change(root / "plugins" / "sitebulb-desktop")
        problems = zip_problems(root, Path(tmp) / "dist")
        check(f"check_zip fails on {label}", any(expect in p for p in problems), True)
        if not any(expect in p for p in problems):
            print("        problems:", problems)


with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    set_demo(root, DEMO)
    out = Path(tmp) / "dist"
    written = release.build(root, "1.0.0", out)
    check("build writes one ZIP for each plugin", sorted(p.name for p in written),
          ["sitebulb-cloud-1.0.0.zip", "sitebulb-desktop-1.0.0.zip"])
    for path in written:
        names = zipfile.ZipFile(path).namelist()
        plugin = path.name.rsplit("-", 1)[0]
        tracked = git(root, "ls-files", f"plugins/{plugin}").splitlines()
        want = sorted(t.split("/", 2)[2] for t in tracked if not t.endswith("/LISTING.md"))
        check(f"{path.name} holds the plugin folder's files at the root, less LISTING.md",
              sorted(names), want)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        check(f"{path.name}.sha256", (out / f"{path.name}.sha256").read_text(),
              f"{digest}  {path.name}\n")
        check(f"{path.name} passes check_zip", check_zip.check(path, "1.0.0", "gitleaks"), [])
    first = (out / "sitebulb-cloud-1.0.0.zip").read_bytes()
    release.build(root, "1.0.0", out)
    check("build makes the same bytes again", (out / "sitebulb-cloud-1.0.0.zip").read_bytes(), first)
    proc = subprocess.run([sys.executable, str(HERE / "check_zip.py"), "--version", "1.0.0",
                           *map(str, written)], capture_output=True, text=True)
    check("CLI check_zip exit 0 on good ZIPs", proc.returncode, 0)
    check("CLI check_zip exit 1 on the wrong version",
          subprocess.run([sys.executable, str(HERE / "check_zip.py"), "--version", "1.0.1",
                          str(written[0])], capture_output=True).returncode, 1)
    check("check_zip fails when gitleaks is missing",
          any("not installed" in p for p in check_zip.check(written[0], "1.0.0", "no-such-gitleaks")),
          True)


def write(rel, text):
    def change(plugin):
        path = plugin / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return change


def manifest(change_data):
    return lambda plugin: edit_json(plugin / ".codex-plugin" / "plugin.json", change_data)


sabotage("a secret", write("skills/sitebulb-dev-handoff/notes.md", f'token = "{secret()}"\n'),
         "gitleaks found a secret")
sabotage("a secret with a gitleaks:allow comment",
         write("notes.md", f'token = "{secret()}" # gitleaks:allow\n'), "gitleaks found a secret")
sabotage("a .gitleaks.toml that turns the rules off",
         write(".gitleaks.toml", "[allowlist]\npaths = ['.*']\n"), "gitleaks configuration")
sabotage("a secret in a file with an image name",
         write("assets/notes.png", f'token = "{secret()}"\n'), "assets/notes.png:1: gitleaks found a secret")
sabotage("a secret in a file with a font name",
         write("assets/font.woff2", f'token = "{secret()}"\n'), "assets/font.woff2:1: gitleaks found a secret")
sabotage("a secret under node_modules/",
         write("node_modules/x/config.txt", f'token = "{secret()}"\n'), "node_modules/x/config.txt:1:")
sabotage("an apps folder", write("apps/app.json", "{}\n"), "apps/ folder")
sabotage("an Apps folder in another letter case", write("Apps/a.json", "{}\n"), "apps/ folder")
sabotage("a .App.json file", write(".App.json", '{"apps": {}}\n'), ".app.json file")
sabotage("a Hooks/Hooks.JSON file", write("Hooks/Hooks.JSON", "{}\n"), "hooks/ folder")
sabotage("a hooks key in .agent-plugin/plugin.json",
         write(".agent-plugin/plugin.json", '{"name": "sitebulb-desktop", "hooks": "./x.json"}\n'),
         ".agent-plugin/plugin.json: declares 'hooks'")
sabotage("an extensions.com.openai.hooks key in a root plugin.json",
         write("plugin.json", '{"extensions": {"com.openai": {"hooks": "./x.json"}}}\n'),
         "plugin.json: declares 'hooks'")
sabotage("a .app.json file", write(".app.json", '{"apps": {}}\n'), ".app.json file")
sabotage("a hooks folder", write("hooks/session_start.py", "print()\n"), "hooks/ folder")
sabotage("a hooks.json file outside hooks/", write("config/hooks.json", "{}\n"), "hooks.json file")
sabotage("a manifest hooks field", manifest(lambda d: d["extensions"]["com.openai"]
                                             .__setitem__("hooks", "./x.json")), "declares 'hooks'")
sabotage("a manifest apps field", manifest(lambda d: d.__setitem__("apps", "./.app.json")),
         "declares 'apps'")
sabotage("the demo URL placeholder", manifest(lambda d: d["extensions"]["com.openai"]["review"]
                                              .__setitem__("demo_recording_url",
                                                           "TODO: unlisted video URL")),
         "demo_recording_url")
sabotage("an http:// demo URL", manifest(lambda d: d["extensions"]["com.openai"]["review"]
                                         .__setitem__("demo_recording_url", "http://example.com/v")),
         "demo_recording_url")
sabotage("a missing demo URL", manifest(lambda d: d["extensions"]["com.openai"]["review"]
                                        .pop("demo_recording_url")), "demo_recording_url")
sabotage("a manifest version that is not the release version",
         lambda plugin: edit_json(plugin / ".cursor-plugin" / "plugin.json",
                                  lambda d: d.__setitem__("version", "0.9.0")), "expected '1.0.0'")
sabotage("release notes for another version",
         manifest(lambda d: d["extensions"]["com.openai"]["publication"]
                  .__setitem__("release_notes", "0.9.0: old")), "release_notes")

with tempfile.TemporaryDirectory() as tmp:
    bad = Path(tmp) / "bad.zip"
    with zipfile.ZipFile(bad, "w") as archive:
        archive.writestr("../escape.txt", "x")
    check("check_zip refuses a '..' path and does not unpack it",
          any("'..'" in p for p in check_zip.check(bad, "1.0.0", "gitleaks")), True)
    check("check_zip wrote nothing outside its folder", (Path(tmp).parent / "escape.txt").exists(), False)
    nested = Path(tmp) / "nested.zip"
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("sitebulb-desktop/.codex-plugin/plugin.json", "{}")
    check("check_zip refuses a ZIP whose manifest is not at the root",
          check_zip.check(nested, "1.0.0", "gitleaks"), [".codex-plugin/plugin.json is not at the ZIP root"])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
