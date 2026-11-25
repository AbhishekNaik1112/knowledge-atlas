---
type: pattern
title: "MCP Over Streamable HTTP"
description: "Hosting a stateless JSON-RPC 2.0 MCP endpoint directly inside an existing FastAPI service."
tags: [ai-systems, mcp, api-design, architecture]
resource: https://modelcontextprotocol.io/
---

# MCP Over Streamable HTTP

Mounting a `POST /mcp` JSON-RPC 2.0 endpoint inside your main web application eliminates separate MCP sidecars and keeps auth, repositories, and database sessions in one place.

## Design Guidelines
- **Stateless Requests:** Authenticate each request via `Authorization: Bearer` without keeping per-user session state in memory.
- **Schema Validation:** Validate tool arguments strictly with Pydantic and apply [agent tool sandboxing](agent-tool-sandboxing.md) boundaries.
- **Zero-Install Clients:** Agents connect immediately using only a URL and Bearer token.
