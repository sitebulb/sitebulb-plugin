# AGENTS.md

Instructions for agents that work in this repository.

## This repository is public

Everything in a file, a commit message, a PR title or body, a PR comment, an issue, a tag or a release note is public and permanent. GitHub keeps the commits of a PR and the earlier versions of a PR description, also after a squash merge or an edit.

Never write any of these items in those places:

- Staff names.
- Internal issue keys or tracker links, for example Linear or Jira.
- Internal tool names or agent names, and notes about the review process.
- Local or internal paths, for example `/tmp`, `/home` or paths in other Sitebulb repositories.
- Internal host names, Vault paths, account or test-account details, and credentials.

## Commits and pull requests

- A commit message has a Conventional Commits subject and a short body for a public reader. Do not add a `Co-Authored-By: Claude` trailer. A repository ruleset refuses a push that contains it.
- A PR body says what changed for users and contributors, and how it was tested. Keep the internal review history in Sitebulb's own systems, not here.
- Never force-push `main`. Never use `--no-verify`.

## Layout

The repository holds one plugin, `sitebulb`, in `plugins/sitebulb`. Its five skills are in `plugins/sitebulb/skills`. The plugin manifests are in `plugins/sitebulb/.claude-plugin`, `plugins/sitebulb/.codex-plugin` and `plugins/sitebulb/.cursor-plugin`. The marketplace files are `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.

## Shared files

`shared/` is the source of the shared engine files. These files are in `shared/references` and `shared/scripts`. Each skill has a copy of the files that it uses. The list of files for each skill is in `scripts/sync_shared.py`.

Do not edit a copy in a skill. Edit the file in `shared/`. Then run `python3 scripts/sync_shared.py` and commit the copies that it changes. `python3 scripts/sync_shared.py --check` writes nothing. It exits 1 when a copy differs from its source, a copy is missing or a source file is missing.

The script does not touch the skill files that only one skill has. These files are `references/document-template.md` in `sitebulb-technical-seo-audit` and `references/pm-tool-mapping.md` in `sitebulb-dev-handoff`. It also does not touch the skill instructions, the manifests or the logo.

## Checks to run before a push

These are the steps in `.github/workflows/ci.yml`. Run them from the repository root. Each step must exit 0.

```bash
python3 shared/scripts/test_score_effort.py
python3 plugins/sitebulb/skills/sitebulb-technical-seo-audit/scripts/test_build_docx.py
python3 scripts/sync_shared.py --check
```

Then run the other three steps as they are written in `ci.yml`. These steps are "Manifests are valid JSON", "Only approved MCP endpoints referenced" and "Skill names are namespaced". "Only approved MCP endpoints referenced" reads every file in the checkout. "Skill names are namespaced" reads every tracked file except `CHANGELOG.md` and `ci.yml`. Both steps read this file.
