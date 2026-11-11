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
- Every PR adds a change fragment. See [`changes/README.md`](changes/README.md).
- To make a release, follow [Making a release](README.md#making-a-release) in the README.
- Never force-push `main`. Never use `--no-verify`.

## Shared files

`shared/` is the only source of the skills, the logo and the engine files. The root `LICENSE` is the source of each plugin's `LICENSE`. Do not edit `plugins/<plugin>/skills/`, `plugins/<plugin>/LICENSE` or `plugins/<plugin>/assets/logo.png`. After a change to `shared/` or `LICENSE`, run `python3 scripts/sync_shared.py` and commit the generated files. The manifests, `.mcp.json`, `README.md` and `LISTING.md` of each plugin are written by hand.

## Checks to run before a push

Run these commands from the repository root. They are the steps in `.github/workflows/ci.yml`:

```bash
python3 scripts/changes.py check --base origin/main
bin=$(mktemp -d) && scripts/install_gitleaks.sh "$bin"   # Linux x64 only
PATH="$bin:$PATH" python3 scripts/test_release.py
python3 scripts/test_changes.py
python3 shared/scripts/test_score_effort.py
python3 shared/skills/sitebulb-technical-seo-audit/scripts/test_build_docx.py
python3 scripts/sync_shared.py --check
python3 scripts/release.py versions
```

Then run the other `ci.yml` steps as they are written in that file. These steps are "Manifests are valid JSON", the MCP server step, the OpenAI and Anthropic listing steps, "claude plugin validate", "Only approved MCP endpoints referenced" and "Skill names are namespaced". Each step must exit 0.
