# Sitebulb Cloud: Anthropic connector listing

This file holds the text for the Listing step of the Claude developer portal
(https://claude.ai/directory/manage) for the Sitebulb Cloud MCP server.
Anthropic cannot edit the description after you submit it. CI checks the
character limits and makes sure that the URLs agree with the plugin manifests.

| Field | Value |
|---|---|
| Server URL | https://cloud.mcp.sitebulb.com/mcp |
| Documentation URL | https://support.sitebulb.com/en/articles/15970977-sitebulb-mcp-start-here |
| Privacy policy URL | https://sitebulb.com/policies/cookie-and-privacy-policy/ |
| Support contact | support@sitebulb.com |
| Icon | assets/logo.png |
| Data access | Read only |

## Name

Sitebulb Cloud

## One-liner

Read-only access to the technical SEO audits in your Sitebulb Cloud account.

## Description

Connect Claude to Sitebulb Cloud to explore the technical SEO audits in your account. Ask about your projects and audits, audit summaries and reports, hints and insights, sample affected URLs, the data for a single URL, history across audits, and what changed between two audits.

Access is read-only, so the connector can't start crawls, change settings or delete data. You sign in to your Sitebulb account with OAuth. You need a Sitebulb Cloud subscription and at least one finished audit.

The Sitebulb Cloud plugin adds five technical SEO skills that use this connector: what to fix first, what changed, technical SEO audit, dev handoff and release check. For Sitebulb Desktop audits, use the separate Sitebulb Desktop connector.
