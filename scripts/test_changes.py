#!/usr/bin/env python3
"""
Tests for changes.py. Each test runs on a git copy of this repository in a
temporary folder, so the version-file exemption reads the real manifests.
Run: python3 scripts/test_changes.py
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import changes  # noqa: E402
import release  # noqa: E402

passed = failed = 0
DAY = dt.date(2026, 11, 11)


def check(name, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {name}\n        got:  {got!r}\n        want: {want!r}")


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
    git(root, "init", "-q")
    git(root, "config", "user.name", "Change tests")
    git(root, "config", "user.email", "tests@example.invalid")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    return root


def commit(root, message="change"):
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)


def gate(root, base):
    """The CI fragment gate: None when it passes, else the error text."""
    try:
        changes.check(root, base)
        return None
    except changes.ChangeError as error:
        return str(error)


def fragment(root, name, text="A change."):
    (root / "changes").mkdir(exist_ok=True)
    (root / "changes" / name).write_text(text + "\n", encoding="utf-8")


# --- fragment names and content -----------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    check("README.md is not a fragment", changes.entries(root), [])
    for name, text, label in [("notes.md", "x", "no date or kind"),
                              ("2026-02-30-bad-date.fixed.md", "x", "impossible date"),
                              ("2026-11-11-Upper.fixed.md", "x", "upper-case slug"),
                              ("2026-11-11-ok.feature.md", "x", "unknown kind"),
                              ("2026-11-11-empty.fixed.md", "  ", "empty text")]:
        fragment(root, name, text)
        try:
            changes.entries(root)
            check(f"rejects {label}", "accepted", "ChangeError")
        except changes.ChangeError:
            passed += 1
        (root / "changes" / name).unlink()
    target = root / "outside.md"
    target.write_text("x")
    (root / "changes" / "2026-11-11-link.docs.md").symlink_to(target)
    try:
        changes.entries(root)
        check("rejects a symbolic link", "accepted", "ChangeError")
    except changes.ChangeError:
        passed += 1
    (root / "changes" / "2026-11-11-link.docs.md").unlink()

    fragment(root, "2026-11-11-b.fixed.md", "Fixed b.")
    fragment(root, "2026-11-10-z.added.md", "Added z.")
    fragment(root, "2026-11-11-a.fixed.md", "Fixed a.")
    check("entries are in kind order, then name order",
          [e[1] for e in changes.entries(root)],
          ["2026-11-10-z.added.md", "2026-11-11-a.fixed.md", "2026-11-11-b.fixed.md"])

# --- new ------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    path = changes.new(root, "fixed", "  Corrected the ZIP path.  ", DAY, None)
    check("new names the file from the message", path.name, "2026-11-11-corrected-the-zip-path.fixed.md")
    check("new writes the trimmed message", path.read_text(), "Corrected the ZIP path.\n")
    try:
        changes.new(root, "fixed", "Corrected the ZIP path.", DAY, None)
        check("new refuses to overwrite a fragment", "overwrote", "ChangeError")
    except changes.ChangeError:
        passed += 1
    try:
        changes.new(root, "docs", "   ", DAY, None)
        check("new refuses an empty message", "accepted", "ChangeError")
    except changes.ChangeError:
        passed += 1
    proc = subprocess.run([sys.executable, str(HERE / "changes.py"), "--root", str(root), "new",
                           "--kind", "docs", "--slug", "readme", "--date", "2026-11-11",
                           "--message", "Documented $(touch SHOULD_NOT_EXIST) `x`."],
                          capture_output=True, text=True)
    check("CLI new exit 0", proc.returncode, 0)
    check("CLI new keeps the message as data",
          (root / "changes" / "2026-11-11-readme.docs.md").read_text(),
          "Documented $(touch SHOULD_NOT_EXIST) `x`.\n")
    check("CLI new runs no shell", (root / "SHOULD_NOT_EXIST").exists(), False)

# --- the CI gate ---------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    base = git(root, "rev-parse", "HEAD")
    check("no diff passes", gate(root, base), None)

    readme = root / "README.md"
    readme.write_text(readme.read_text() + "\nMore.\n")
    commit(root)
    check("a change without a fragment fails",
          "needs a new fragment" in (gate(root, base) or ""), True)
    proc = subprocess.run([sys.executable, str(HERE / "changes.py"), "--root", str(root),
                           "check", "--base", base], capture_output=True, text=True)
    check("CLI check --base exit 1 without a fragment", proc.returncode, 1)

    fragment(root, "2026-11-11-readme.docs.md", "Documented more.")
    commit(root)
    check("the same change with a fragment passes", gate(root, base), None)

    base = git(root, "rev-parse", "HEAD")
    (root / "changes" / "2026-11-11-readme.docs.md").write_text("Edited.\n")
    commit(root)
    check("editing an existing fragment is not a new fragment",
          gate(root, base) is not None, True)

    for label, change in (
            ("renaming", lambda: git(root, "mv", "changes/2026-11-11-readme.docs.md",
                                     "changes/2026-11-12-readme.docs.md")),
            ("copying", lambda: (root / "changes/2026-11-12-copy.docs.md").write_text(
                (root / "changes/2026-11-11-readme.docs.md").read_text()))):
        git(root, "reset", "-q", "--hard", base)
        change()
        readme.write_text(readme.read_text() + f"\n{label}\n")
        commit(root)
        check(f"{label} an existing fragment beside a change is not a new fragment",
              "needs a new fragment" in (gate(root, base) or ""), True)
    git(root, "reset", "-q", "--hard", base)
    git(root, "mv", "changes/2026-11-11-readme.docs.md", "changes/2026-11-12-readme.docs.md")
    commit(root)
    check("renaming a fragment alone is not a new fragment",
          "needs a new fragment" in (gate(root, base) or ""), True)

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    base = git(root, "rev-parse", "HEAD")
    log = root / "CHANGELOG.md"
    log.write_text(log.read_text().replace("Changelog", "Changelog\n", 1))
    commit(root)
    check("a change to CHANGELOG.md alone passes", gate(root, base), None)

with tempfile.TemporaryDirectory() as tmp:
    root = copy_repo(tmp)
    fragment(root, "2026-11-11-feature.added.md", "Added a feature.")
    commit(root)
    base = git(root, "rev-parse", "HEAD")
    release.prepare(root, "1.1.0", DAY)
    commit(root, "prepare 1.1.0")
    check("the diff of release.py prepare passes", gate(root, base), None)

    base = git(root, "rev-parse", "HEAD")
    codex = root / "plugins/sitebulb-cloud/.codex-plugin/plugin.json"
    codex.write_text(codex.read_text().replace('"Sitebulb Cloud"', '"Sitebulb Cloud X"', 1))
    commit(root)
    check("a manifest change beside the version fields fails", gate(root, base) is not None, True)

    base = git(root, "rev-parse", "HEAD")
    data = json.loads(codex.read_text())
    data["version"] = "1.1.1"
    codex.write_text(json.dumps(data, indent=2) + "\n")
    commit(root)
    check("a version-only manifest change passes", gate(root, base), None)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
