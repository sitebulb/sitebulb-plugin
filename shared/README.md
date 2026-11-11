# Shared sources (single source of truth)

The repository ships two plugins, `plugins/sitebulb-desktop` and `plugins/sitebulb-cloud`, with the same five skills. Each plugin folder must be complete on its own, because the plugin directories (Claude, Codex/OpenAI, Cursor) take one plugin folder at a time and refuse symbolic links and paths outside it. So each plugin carries a copy of every skill. **This directory is the single source of truth** — edit here, then run:

```
python3 scripts/sync_shared.py
```

Never edit a plugin's copy directly; CI fails on drift (`sync_shared.py --check`), including a file in a plugin's `skills/` folder that no source here produces. Which skill consumes which engine file is defined in the manifest inside `scripts/sync_shared.py`.

## Contents

- `skills/<skill>/` — the files that belong to one skill: `SKILL.md`, its `README.md`, and skill-local files (`sitebulb-technical-seo-audit/references/document-template.md` and `scripts/build_docx.py` with its test suite, `sitebulb-dev-handoff/references/pm-tool-mapping.md`). Each is copied to the same path under both plugins.
- `references/shared-core.md` — the Sitebulb MCP data-handling rules (noise filtering, sample semantics, delta semantics, tool-binding preflight) and the framing-interview protocol.
- `references/effort-scoring.md` — the effort/impact scoring spec: fix archetypes, volume bands, modifiers, durations.
- `references/context-emphasis.md` — the context reframe rules (business type, situation, precedence).
- `references/hint-map.csv` — the classified hint catalogue (358 hints, `url_filter_id`-keyed). Generated from the internal workbook `All_Sitebulb_Hints_with_Effort_Archetypes.xlsx` (maintained outside this repo); regenerate the CSV from the workbook rather than editing rows by hand.
- `scripts/score_effort.py` — the deterministic two-axis scorer implementing `effort-scoring.md`.
- `scripts/test_score_effort.py` — its test suite (`python3 shared/scripts/test_score_effort.py`).
- `assets/logo.png` — the logo of both plugins.

The repository root `LICENSE` is also copied into each plugin. Each plugin's manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`), `.mcp.json` and `README.md` differ between the plugins, so they are written by hand in the plugin folder and the sync never touches them.
