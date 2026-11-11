# Sitebulb Skills

Official Sitebulb plugins for AI coding agents: five technical-SEO skills that work directly with your Sitebulb Desktop or Cloud audit data. Ask your assistant what to fix first, what changed since the last crawl, produce a client-ready audit document, raise dev tickets, or run your post-release check — all grounded in your real crawl data, never guesswork.

Works in [Claude Code](https://claude.com/claude-code), Codex, Cursor, GitHub Copilot, and other agents that read the open SKILL.md plugin format.

## Choose your plugin

There is one plugin for each Sitebulb product. Each plugin has the same five skills and connects to the MCP server of its product:

| Plugin | For | MCP server |
|---|---|---|
| `sitebulb-desktop` | Audits in Sitebulb Desktop on your computer | `https://desktop.mcp.sitebulb.com/mcp` |
| `sitebulb-cloud` | Audits in your Sitebulb Cloud account | `https://cloud.mcp.sitebulb.com/mcp` |

Install the plugin for the product you use. If you use both products, you can install both plugins. Then the skills ask which product to use.

### Upgrading from the `sitebulb` plugin

The `sitebulb` plugin (last release 0.2.0) is replaced by `sitebulb-desktop` and `sitebulb-cloud`. If you installed `sitebulb`:

1. Uninstall `sitebulb`. If you keep it, your assistant has each skill two times.
   - **Claude Code:** `/plugin uninstall sitebulb@sitebulb`, or `claude plugin uninstall sitebulb@sitebulb` from a terminal.
   - **Codex:** in the Codex app, open the plugin and select **Uninstall plugin**. In Codex CLI, enter `/plugins` and uninstall **Sitebulb** in the plugin browser.
   - **Cursor, GitHub Copilot and other agents:** remove it in the plugin settings of your assistant. In Cursor, installed plugins are under **Customize** in the sidebar.
2. Install `sitebulb-desktop` or `sitebulb-cloud` for your product, as shown below.
3. If you added the Sitebulb MCP to your assistant yourself, for example as a custom connector, remove it. The new plugin connects its own server, and two connections give your assistant two sets of the same tools.

## Installation

The examples install `sitebulb-desktop`. For Sitebulb Cloud, write `sitebulb-cloud` in its place.

### Claude Code

```
/plugin marketplace add sitebulb/sitebulb-plugin
/plugin install sitebulb-desktop@sitebulb
```

### Codex

**Codex app:** open **Plugins** from the sidebar, choose **Add plugin marketplace**, enter `sitebulb/sitebulb-plugin` as the source (Git ref `main`), then install **Sitebulb Desktop** or **Sitebulb Cloud** and restart Codex.

**Codex CLI:**

```bash
codex plugin marketplace add sitebulb/sitebulb-plugin
codex plugin add sitebulb-desktop@sitebulb
```

### Cursor

In Cursor Agent chat:

```
/add-plugin sitebulb-desktop
```

Or search for "Sitebulb" in the plugin marketplace.

### GitHub Copilot

**Copilot CLI** (inside the CLI, or from a shell with the `copilot` binary prefixed by `copilot`):

```
/plugin marketplace add sitebulb/sitebulb-plugin
/plugin install sitebulb-desktop@sitebulb
```

**VS Code:** run `Chat: Install Plugin from Source` from the command palette, enter `sitebulb/sitebulb-plugin`, and select **sitebulb-desktop** or **sitebulb-cloud**.

### Other agents

Any agent that reads Claude-compatible plugin manifests installs this repo directly — for example:

```bash
droid plugin marketplace add https://github.com/sitebulb/sitebulb-plugin && droid plugin install sitebulb-desktop@sitebulb
qwen extensions install sitebulb/sitebulb-plugin:sitebulb-desktop
grok plugin marketplace add sitebulb/sitebulb-plugin && grok plugin install sitebulb-desktop
```

## Connecting to Sitebulb

Each plugin declares its MCP server: `https://desktop.mcp.sitebulb.com/mcp` for Sitebulb Desktop or `https://cloud.mcp.sitebulb.com/mcp` for Sitebulb Cloud. When a skill first reads your audits, your assistant asks you to sign in to your Sitebulb account with OAuth. Sitebulb Desktop must be open and running on your computer for the Desktop server to read your audits.

If your assistant does not connect the server from the plugin, connect it yourself with the guide for your assistant. If a skill runs before the MCP is connected, it points you at the same guide:

**→ [Sitebulb MCP: Start Here](https://support.sitebulb.com/en/articles/15970977-sitebulb-mcp-start-here)**

**Requirements:** a Sitebulb Desktop or Sitebulb Cloud licence, at least one finished audit in the project you want to work with, and `python3` available to the agent (the skills bundle small stdlib-only scripts for scoring and document generation). The connection is read-only — skills can read your audits but never trigger crawls.

## The skills

Both plugins have all five skills, because Sitebulb Desktop and Sitebulb Cloud give the skills the same tools. The table uses the Desktop plugin's prefix. In the Cloud plugin, the prefix is `sitebulb-cloud:`.

| Skill | What it does | Try |
|---|---|---|
| `sitebulb-desktop:sitebulb-what-to-fix-first` | Prioritised triage: the 3–5 issue clusters most worth fixing for your business, impact vs effort | "What should I fix first on this site?" |
| `sitebulb-desktop:sitebulb-what-changed` | The change story between your two most recent audits — wins, regressions, watch-list | "What changed since the last crawl?" |
| `sitebulb-desktop:sitebulb-technical-seo-audit` | A focused client-facing audit document (.docx working draft, 5–10 issues) shaped by why the audit was commissioned | "Write up the audit for [client]" |
| `sitebulb-desktop:sitebulb-dev-handoff` | Dev-ready tickets from audit findings, pushed to your connected PM tool | "Send these to Jira" / "Ticket the quick wins" |
| `sitebulb-desktop:sitebulb-release-check` | Your configured post-release watch-list check with thresholds and breach alerts | "Run my Tuesday check" |

Skills trigger automatically when you ask for the matching work — you don't need to invoke them by name.

## Optional integrations

Some features light up when other tools are connected:

- **A PM-tool MCP** (Jira, Linear, Asana, Monday, ClickUp) lets `sitebulb-dev-handoff` create tickets directly. Without one, it produces ready-to-paste markdown ticket bodies.
- **A messaging MCP** (Slack, Teams, …) lets `sitebulb-release-check` post breach alerts to a channel. Without one, alerts appear in chat.
- **Google Analytics / Search Console connected inside Sitebulb** lets `sitebulb-what-to-fix-first` and `sitebulb-technical-seo-audit` weight priorities by real traffic, and gives `sitebulb-what-changed` a search-performance overlay.

## Licence

MIT — see [LICENSE](LICENSE). © Sitebulb Ltd.

## Contributing / maintenance

`plugins/sitebulb-desktop/` and `plugins/sitebulb-cloud/` must each be complete on their own: the plugin directories install, validate and package one plugin folder at a time, and refuse symbolic links and paths outside the folder. So each plugin carries a copy of the skills, the licence and the logo, generated from [`shared/`](shared/README.md). Edit there and run `python3 scripts/sync_shared.py`. Each plugin's manifests, `.mcp.json`, `README.md` and `LISTING.md` are written by hand. CI enforces sync, runs the test suites, validates the manifests, and runs `claude plugin validate` on each plugin.

### Directory listings

Each plugin has the text for two directory listings:

- **OpenAI plugin directory:** `.codex-plugin/plugin.json` holds the listing fields in `interface`, and the review test cases and release notes in `extensions.com.openai`. The release workflow builds the upload ZIP for each plugin from its plugin folder (see [Making a release](#making-a-release)). This repository uses the Codex format only, so CI refuses a root `plugin.json` or `mcp.json` in a plugin folder. A root `plugin.json` with an `extensions.com.openai` object replaces the OpenAI settings in `.codex-plugin/plugin.json`, and a root `mcp.json` is a second MCP declaration.
- **Anthropic connector directory:** `LISTING.md` holds the name, one-liner, description and links for the Listing step of the Claude developer portal.

CI checks both against the published character limits and URL rules. Before an upload, replace the `demo_recording_url` placeholder with the URL of the walkthrough video.

### Change fragments

Each pull request adds a change fragment, a file in [`changes/`](changes/README.md) with one sentence or more for the changelog:

```bash
python3 scripts/changes.py new --kind fixed --message "Corrected the Cloud plugin's support URL."
```

CI fails a pull request that changes files and adds no fragment. A change to `CHANGELOG.md` alone, or the version changes that `scripts/release.py prepare` makes, needs no fragment.

### Making a release

1. On a branch from `main`, run `python3 scripts/release.py prepare <X.Y.Z>`. The command does these steps:
   - It sets the version in each plugin's three manifests and in `.cursor-plugin/marketplace.json`.
   - It adds a `## <X.Y.Z> — <date>` section with the text of each fragment to the top of `CHANGELOG.md`.
   - It writes the same text, after `<X.Y.Z>: `, to `publication.release_notes` in both Codex manifests.
   - It deletes the fragments.
2. Read the new `CHANGELOG.md` section. OpenAI shows the release notes to its reviewers, so edit the section and the two `release_notes` fields together if necessary.
3. Before the release goes to OpenAI, set `demo_recording_url` in both Codex manifests to the URL of the walkthrough video. The release check refuses the placeholder.
4. Open a pull request and merge it.
5. Tag the merge commit on `main` and push the tag:

   ```bash
   git tag v<X.Y.Z> origin/main
   git push origin v<X.Y.Z>
   ```

6. The tag starts the Release workflow. The workflow fails when the tagged commit is not on `main`, or when a version field is not `<X.Y.Z>`. Then it builds `sitebulb-desktop-<X.Y.Z>.zip` and `sitebulb-cloud-<X.Y.Z>.zip` and checks each ZIP. The check fails on these items:
   - A secret that gitleaks finds.
   - An `apps` or `hooks` folder, a `.app.json` or `hooks.json` file, or a manifest that declares `apps` or `hooks`.
   - A `demo_recording_url` that is not an `https://` URL.
7. The workflow attaches the ZIPs and their `.sha256` files to a draft GitHub release for the tag. Download each ZIP, upload it to the OpenAI plugin portal, then publish the draft release. The workflow uploads nothing to OpenAI or Anthropic.

Each ZIP holds the contents of the plugin folder at the ZIP root, without `LISTING.md`. You can run the same steps on your computer, with gitleaks installed:

```bash
python3 scripts/release.py check-tag v<X.Y.Z>
python3 scripts/release.py build <X.Y.Z> --out dist
python3 scripts/check_zip.py --version <X.Y.Z> dist/*.zip
```
