# PM-Tool Field Mapping

The skill is tool-agnostic: it detects which PM MCP is connected and maps the ticket anatomy onto that tool's fields. MCP schemas change — **discover at runtime**: read the connected tool's actual create/update tool schemas before mapping, and treat this file as orientation, not gospel. Anything that won't map cleanly goes into the ticket body as labelled text rather than being dropped. (Same discipline as the Sitebulb side — see shared-core § Tool binding.)

## Universal mapping

| Ticket anatomy | Maps to |
|---|---|
| Title | summary / title / name |
| Body (what's wrong → provenance) | description / notes, in the tool's richest supported text format |
| Priority | the tool's priority field where one exists; otherwise a label or body line |
| `sitebulb` marker | label / tag / nearest equivalent (see below) |
| Provenance line | plain text, last line of the body — never a custom field |

## Per-tool notes

**Jira (Atlassian MCP):** label via `additional_fields: {"labels": ["sitebulb"]}`; priority via `additional_fields: {"priority": {"name": "High"}}` — priority names vary per instance, so on rejection fetch the project's valid values. Description accepts markdown. Components/epic only if the user named them in framing. Full affected-URL lists are never attached — every ticket carries the Sitebulb-export pointer line instead (SKILL.md step 8).

**Linear:** `sitebulb` label (create it if absent, with permission); priority is an integer 0–4 (1 = urgent); markdown descriptions.

**Asana:** tags instead of labels; no native priority field — use a priority custom field if the board has one, otherwise a body line; "notes" field is plain text unless html_notes is available.

**Monday:** items with per-board column values — boards differ wildly, so ask the user which column is priority/status rather than guessing; tags column for the `sitebulb` marker.

**ClickUp:** tags; priority is an integer 1–4 (1 = urgent); markdown descriptions.

## The `sitebulb` marker

Apply the marker (label, tag, or tags column) so the user can filter Sitebulb-raised tickets in their PM tool later. It's a convenience, not load-bearing — if a tool offers no label/tag mechanism, skip it rather than contriving one.
