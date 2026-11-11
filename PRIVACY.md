# Privacy & Data Handling

This repository contains two plugins for AI coding agents, `sitebulb-desktop`
and `sitebulb-cloud`. Each plugin has markdown skill instructions, small Python
scripts (an effort scorer and a Word-document builder) that run locally using
only the Python standard library, and the address of one Sitebulb MCP server.

## Summary

- The plugins contain no telemetry or analytics code.
- The plugins run no background service and upload nothing automatically.
- The bundled scripts make no network requests — they read local input and
  write local output.
- Data leaves your machine only when your AI host or an integration you have
  explicitly connected performs a network request.

## What may send data

1. **Your AI host and its model provider.** Running these skills in Claude
   Code, Codex, Cursor, GitHub Copilot, or any other agent means that host
   sends prompts and context — including audit data the skills have read — to
   its configured model provider. That behaviour is controlled by the host and
   provider, not by these plugins.

2. **The Sitebulb MCP.** Each plugin declares one Sitebulb MCP server:
   `https://desktop.mcp.sitebulb.com/mcp` for `sitebulb-desktop` and
   `https://cloud.mcp.sitebulb.com/mcp` for `sitebulb-cloud`. When you sign in
   and a skill runs, your agent reads audit data from that server over an
   OAuth-authorised, read-only connection. If you connected the Sitebulb MCP yourself
   as a custom connector, your agent reads from `https://mcp.sitebulb.com/desktop`
   or `https://mcp.sitebulb.com/cloud` instead, in the same way. Sitebulb's
   handling of that data is governed by the
   [Sitebulb privacy policy](https://sitebulb.com/policies/cookie-and-privacy-policy/).

3. **Optional integrations you connect.** The `sitebulb-dev-handoff` skill can create
   tickets through a project-management MCP (Jira, Linear, Asana, Monday,
   ClickUp) and `sitebulb-release-check` can post alerts through a messaging MCP
   (Slack, Teams). These are used only when you invoke the matching skill and
   are governed by those services' own policies. If you do not connect them,
   nothing is sent to them.

## Data ownership and retention

This repository operates no backend service and stores none of your data.
Documents the skills generate (for example audit `.docx` files) are written to
your local machine. Retention and processing for model prompts, the Sitebulb
MCP, and optional integrations are governed by those external services.

## Security reporting

If you identify a security issue in this repository, follow the disclosure
process in [SECURITY.md](SECURITY.md).
