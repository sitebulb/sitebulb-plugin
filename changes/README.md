# Change fragments

Each pull request adds one fragment here for each change that a user, a reviewer or a maintainer can see. `scripts/release.py prepare` moves the fragments into `CHANGELOG.md` and into the Codex release notes, then deletes them. So this folder holds only the changes that no release has shipped.

## Add a fragment

From the repository root:

```bash
python3 scripts/changes.py new --kind fixed --message "Corrected the Cloud plugin's support URL."
```

The command writes `changes/<YYYY-MM-DD>-<slug>.<kind>.md`. The kind is one of `added`, `changed`, `fixed`, `removed`, `security`, `docs` or `maintenance`. Write the text for a plugin user: what changed and why it matters to them. The text goes into the changelog and into the release notes that OpenAI reads, without the kind.

A fragment can have more than one paragraph, and a list with `- ` items. In `CHANGELOG.md`, each paragraph and each list item becomes one bullet. A list after a line that ends in ":" goes under that line. In the release notes, the text becomes plain sentences.

## The CI check

CI fails a pull request that changes files and adds no new fragment. A fragment is new only when no fragment at the base has the same text, so a renamed or copied fragment does not count. A pull request needs no fragment when each file that it changes is one of these:

- `CHANGELOG.md`.
- A fragment that the pull request deletes.
- A version file in which only `version` or `publication.release_notes` changes.

`release.py prepare` makes this kind of change. Run the check yourself with `python3 scripts/changes.py check --base origin/main`.
