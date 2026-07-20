# Shared engine (canonical source)

The five skills ship self-contained copies of the shared Sitebulb engine so any skill folder can be distributed standalone. **This directory is the single source of truth** — edit here, then run:

```
python3 scripts/sync_shared.py
```

Never edit a skill's copy directly; CI fails on drift (`sync_shared.py --check`). Which skill consumes which file is defined in the manifest inside `scripts/sync_shared.py`.

## Contents

- `references/shared-core.md` — the Sitebulb MCP data-handling rules (noise filtering, sample semantics, delta semantics, tool-binding preflight) and the framing-interview protocol.
- `references/effort-scoring.md` — the effort/impact scoring spec: fix archetypes, volume bands, modifiers, durations.
- `references/context-emphasis.md` — the context reframe rules (business type, situation, precedence).
- `references/hint-map.csv` — the classified hint catalogue (358 hints, `url_filter_id`-keyed). Generated from the internal workbook `All_Sitebulb_Hints_with_Effort_Archetypes.xlsx` (maintained outside this repo); regenerate the CSV from the workbook rather than editing rows by hand.
- `scripts/score_effort.py` — the deterministic two-axis scorer implementing `effort-scoring.md`.
- `scripts/test_score_effort.py` — its test suite (`python3 scripts/test_score_effort.py`).

Skill-local files (`technical-seo-audit/references/document-template.md`, `dev-handoff/references/pm-tool-mapping.md`) are not shared and are never touched by the sync.
